"""
Intraday Bounds Prediction Models

Implements quantile regression for predicting upper/lower price bounds.
Supports both gradient boosting (XGBoost/LightGBM) and linear baselines (Ridge).
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List, Any
import logging
import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_pinball_loss

logger = logging.getLogger(__name__)

# Try to import XGBoost and LightGBM (optional dependencies)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available, using Ridge baseline only")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not available")


class QuantileGBM:
    """Gradient Boosting for Quantile Regression."""
    
    def __init__(
        self,
        quantiles: Tuple[float, ...] = (0.1, 0.9),
        model_type: str = 'xgboost',
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        random_state: int = 42
    ):
        """
        Initialize quantile GBM model.
        
        Args:
            quantiles: Quantiles to predict (e.g., (0.1, 0.9) for 10th and 90th percentile)
            model_type: 'xgboost' or 'lightgbm'
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Learning rate
            random_state: Random seed
        """
        self.quantiles = quantiles
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        
        self.models: Dict[float, Any] = {}
        self.scaler = StandardScaler()
        self.feature_names: Optional[List[str]] = None
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'QuantileGBM':
        """
        Fit quantile models.
        
        Args:
            X: Feature matrix
            y: Target values (actual high or low prices)
            
        Returns:
            self
        """
        self.feature_names = list(X.columns)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train a model for each quantile
        for q in self.quantiles:
            logger.info(f"Training {self.model_type} for quantile {q}")
            
            if self.model_type == 'xgboost' and XGBOOST_AVAILABLE:
                model = xgb.XGBRegressor(
                    objective=f'reg:quantileerror',
                    quantile_alpha=q,
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    learning_rate=self.learning_rate,
                    random_state=self.random_state,
                    n_jobs=-1
                )
            elif self.model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
                model = lgb.LGBMRegressor(
                    objective='quantile',
                    alpha=q,
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    learning_rate=self.learning_rate,
                    random_state=self.random_state,
                    n_jobs=-1,
                    verbose=-1
                )
            else:
                raise ValueError(f"Model type {self.model_type} not available")
            
            model.fit(X_scaled, y)
            self.models[q] = model
        
        return self
    
    def predict(self, X: pd.DataFrame) -> Dict[float, np.ndarray]:
        """
        Predict quantiles.
        
        Args:
            X: Feature matrix
            
        Returns:
            Dict mapping quantile to predictions
        """
        X_scaled = self.scaler.transform(X)
        
        predictions = {}
        for q, model in self.models.items():
            predictions[q] = model.predict(X_scaled)
        
        return predictions
    
    def get_feature_importance(self, quantile: float = 0.9) -> pd.Series:
        """Get feature importance for a specific quantile model."""
        if quantile not in self.models:
            raise ValueError(f"Quantile {quantile} not trained")
        
        model = self.models[quantile]
        
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        else:
            importance = np.zeros(len(self.feature_names))
        
        return pd.Series(importance, index=self.feature_names).sort_values(ascending=False)


class RidgeQuantile:
    """Ridge Regression baseline for quantile prediction."""
    
    def __init__(
        self,
        quantiles: Tuple[float, ...] = (0.1, 0.9),
        alpha: float = 1.0,
        random_state: int = 42
    ):
        """
        Initialize Ridge quantile model.
        
        Args:
            quantiles: Quantiles to predict
            alpha: Regularization strength
            random_state: Random seed
        """
        self.quantiles = quantiles
        self.alpha = alpha
        self.random_state = random_state
        
        self.models: Dict[float, Ridge] = {}
        self.scaler = StandardScaler()
        self.feature_names: Optional[List[str]] = None
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'RidgeQuantile':
        """
        Fit Ridge models.
        
        For quantile regression with Ridge, we approximate by:
        - Lower quantile (q=0.1): predict y - k*std(y)
        - Upper quantile (q=0.9): predict y + k*std(y)
        where k is chosen based on normal distribution quantiles
        
        Args:
            X: Feature matrix
            y: Target values
            
        Returns:
            self
        """
        self.feature_names = list(X.columns)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train base model
        base_model = Ridge(alpha=self.alpha, random_state=self.random_state)
        base_model.fit(X_scaled, y)
        
        # For each quantile, adjust predictions
        for q in self.quantiles:
            # Use normal distribution to approximate quantile
            from scipy import stats
            z_score = stats.norm.ppf(q)
            
            # Create adjusted target
            y_std = y.std()
            y_adjusted = y + z_score * y_std * 0.5  # Scale factor for stability
            
            model = Ridge(alpha=self.alpha, random_state=self.random_state)
            model.fit(X_scaled, y_adjusted)
            self.models[q] = model
        
        return self
    
    def predict(self, X: pd.DataFrame) -> Dict[float, np.ndarray]:
        """Predict quantiles."""
        X_scaled = self.scaler.transform(X)
        
        predictions = {}
        for q, model in self.models.items():
            predictions[q] = model.predict(X_scaled)
        
        return predictions


def fit_quantile_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    quantiles: Tuple[float, ...] = (0.1, 0.9),
    model_type: str = 'xgboost'
) -> QuantileGBM | RidgeQuantile:
    """
    Fit quantile regression model.
    
    Args:
        X_train: Training features
        y_train: Training targets
        quantiles: Quantiles to predict
        model_type: 'xgboost', 'lightgbm', or 'ridge'
        
    Returns:
        Fitted model
    """
    if model_type == 'ridge':
        model = RidgeQuantile(quantiles=quantiles)
    elif model_type in ['xgboost', 'lightgbm']:
        model = QuantileGBM(quantiles=quantiles, model_type=model_type)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    
    model.fit(X_train, y_train)
    return model


def evaluate_quantile_model(
    model: QuantileGBM | RidgeQuantile,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    current_prices: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Evaluate quantile model performance.
    
    Metrics:
    - Pinball loss (quantile loss)
    - MAE for each quantile
    - Coverage (% of actual values within predicted band)
    - Average band width
    
    Args:
        model: Trained quantile model
        X_test: Test features
        y_test: Test targets (actual high/low)
        current_prices: Current prices for band width calculation
        
    Returns:
        Dict of metrics
    """
    predictions = model.predict(X_test)
    
    metrics = {}
    
    # Pinball loss and MAE for each quantile
    for q, y_pred in predictions.items():
        pinball = mean_pinball_loss(y_test, y_pred, alpha=q)
        mae = mean_absolute_error(y_test, y_pred)
        
        metrics[f'pinball_q{int(q*100)}'] = pinball
        metrics[f'mae_q{int(q*100)}'] = mae
    
    # Coverage (for band between lower and upper quantiles)
    if len(predictions) >= 2:
        quantiles_sorted = sorted(predictions.keys())
        lower_q = quantiles_sorted[0]
        upper_q = quantiles_sorted[-1]
        
        lower_pred = predictions[lower_q]
        upper_pred = predictions[upper_q]
        
        # Check if actual values fall within band
        within_band = (y_test >= lower_pred) & (y_test <= upper_pred)
        coverage = within_band.mean()
        metrics['coverage'] = coverage
        
        # Average band width
        band_width = upper_pred - lower_pred
        metrics['avg_band_width'] = band_width.mean()
        
        # Band width as % of price (if current_prices provided)
        if current_prices is not None:
            band_width_pct = (band_width / current_prices) * 100
            metrics['avg_band_width_pct'] = band_width_pct.mean()
    
    return metrics


def save_model(
    model: QuantileGBM | RidgeQuantile,
    path: Path,
    metadata: Optional[Dict] = None
) -> None:
    """Save model with metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    model_data = {
        'model': model,
        'metadata': metadata or {}
    }
    
    joblib.dump(model_data, path, compress=3)
    logger.info(f"Model saved to {path}")


def load_model(path: Path) -> Tuple[QuantileGBM | RidgeQuantile, Dict]:
    """Load model and metadata."""
    model_data = joblib.load(path)
    return model_data['model'], model_data.get('metadata', {})

