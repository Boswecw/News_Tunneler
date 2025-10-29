"""
ML training for trading signals.

Trains a logistic regression model to predict which signals beat the market.
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from app.core.db import get_db_context
from app.models.signal import Signal
from app.models.model_run import ModelRun

logger = logging.getLogger(__name__)

# Feature columns for training
FEATURE_COLS = [
    "sentiment",
    "magnitude",
    "novelty",
    "credibility",
    "ret_1d",
    "vol_z",
    "vwap_dev",
    "gap_pct",
    "sector_momo_pct",
    "earnings_in_days",
]

# Path to save model weights
MODEL_WEIGHTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "model_weights.json"
)


def train_model(min_samples: int = 50) -> Optional[Dict]:
    """
    Train logistic regression model on labeled signals.
    
    Steps:
    1. Load labeled signals from database
    2. Extract features and labels
    3. Train LogisticRegression with StandardScaler
    4. Extract feature weights (coefficients)
    5. Save weights to data/model_weights.json
    6. Create ModelRun record
    
    Args:
        min_samples: Minimum number of labeled samples required
        
    Returns:
        Dict with training results or None if insufficient data
    """
    logger.info("Starting model training")
    
    with get_db_context() as db:
        # Load labeled signals
        labeled = db.query(Signal).filter(Signal.y_beat.isnot(None)).all()
        
        if len(labeled) < min_samples:
            logger.warning(
                f"Insufficient data for training: {len(labeled)} < {min_samples}"
            )
            return None
        
        logger.info(f"Training on {len(labeled)} labeled signals")
        
        # Convert to DataFrame
        data = []
        for sig in labeled:
            row = {"y_beat": sig.y_beat}
            for col in FEATURE_COLS:
                row[col] = sig.features.get(col, 0.0)
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Prepare features and labels
        X = df[FEATURE_COLS].fillna(0)
        y = df["y_beat"]
        
        # Train model
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_scaled, y)
        
        # Extract weights (scale back to original feature scale)
        # Weight = coefficient / std_dev
        weights = {}
        for i, col in enumerate(FEATURE_COLS):
            coef = model.coef_[0][i]
            std = scaler.scale_[i]
            # Scale to make weights interpretable (multiply by 10 for readability)
            weights[col] = float(coef / std * 10)
        
        # Calculate metrics
        accuracy = model.score(X_scaled, y)
        class_balance = y.mean()
        
        metrics = {
            "n_rows": len(labeled),
            "accuracy": float(accuracy),
            "class_balance": float(class_balance),
            "features": FEATURE_COLS,
        }
        
        # Save weights to file
        os.makedirs(os.path.dirname(MODEL_WEIGHTS_PATH), exist_ok=True)
        with open(MODEL_WEIGHTS_PATH, "w") as f:
            json.dump(weights, f, indent=2)
        
        logger.info(f"Saved model weights to {MODEL_WEIGHTS_PATH}")
        logger.info(f"Accuracy: {accuracy:.3f}, Class balance: {class_balance:.3f}")
        
        # Create ModelRun record
        version = f"v{datetime.now().strftime('%Y%m%d')}"
        
        # Check if version exists
        existing = db.query(ModelRun).filter(ModelRun.version == version).first()
        if existing:
            # Update existing
            existing.weights = weights
            existing.metrics = metrics
            db.add(existing)
        else:
            # Create new
            model_run = ModelRun(
                version=version,
                weights=weights,
                metrics=metrics,
            )
            db.add(model_run)
        
        db.commit()
        
        logger.info(f"Created ModelRun record: {version}")
        
        return {
            "version": version,
            "weights": weights,
            "metrics": metrics,
        }

