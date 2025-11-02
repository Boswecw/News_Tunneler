"""
Online self-training research model using River.

This model continuously learns from realized market outcomes
without requiring batch retraining.
"""
import json
import pathlib
import threading
from typing import Dict, Any, Optional

from river import compose, preprocessing, linear_model, optim, metrics

from app.core.logging import logger


# Model persistence path
MODEL_PATH = pathlib.Path("model_store/research_model.json")

# Thread lock for model updates
LOCK = threading.Lock()


def build_pipeline():
    """
    Build River pipeline for online learning.
    
    Pipeline:
    1. OneHotEncoder - handles categorical features
    2. StandardScaler - normalizes numeric features
    3. LogisticRegression - binary classification with SGD
    """
    return compose.Pipeline(
        preprocessing.OneHotEncoder() |
        preprocessing.StandardScaler() |
        linear_model.LogisticRegression(
            optimizer=optim.SGD(0.01),
            l2=1e-4
        )
    )


class ResearchModel:
    """
    Self-training research model for predicting 3-day price movements.
    
    Uses online learning to continuously improve from market outcomes.
    Thread-safe for concurrent predictions and updates.
    """
    
    def __init__(self):
        """Initialize model with fresh pipeline."""
        self.clf = build_pipeline()
        self.log_loss = metrics.LogLoss()
        self.n_samples = 0
        
    def predict_proba(self, x: Dict[str, Any]) -> float:
        """
        Predict probability of positive 3-day return.
        
        Args:
            x: Feature dict from featurize()
            
        Returns:
            Probability in [0, 1]
        """
        with LOCK:
            try:
                proba_dict = self.clf.predict_proba_one(x)
                return float(proba_dict.get(True, 0.0))
            except Exception as e:
                logger.error(f"Prediction error: {e}")
                return 0.5  # Neutral prediction on error
    
    def learn_one(self, x: Dict[str, Any], y: int):
        """
        Update model with one training example.

        Args:
            x: Feature dict
            y: Label (0 or 1)
        """
        with LOCK:
            try:
                # Update model
                self.clf.learn_one(x, y)

                # Update metrics
                proba_dict = self.clf.predict_proba_one(x)
                prob_true = proba_dict.get(True, 0.0)
                self.log_loss.update(bool(y), prob_true)

                self.n_samples += 1

                if self.n_samples % 100 == 0:
                    logger.info(f"Model trained on {self.n_samples} samples, LogLoss: {self.log_loss.get():.4f}")

            except Exception as e:
                logger.error(f"Training error: {e}")
    
    def save(self, path: Optional[pathlib.Path] = None):
        """
        Save model to disk.
        
        Args:
            path: Optional custom path (defaults to MODEL_PATH)
        """
        save_path = path or MODEL_PATH
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with LOCK:
            try:
                model_dict = self.clf.to_dict()
                model_dict["_meta"] = {
                    "n_samples": self.n_samples,
                    "log_loss": self.log_loss.get() if self.n_samples > 0 else None
                }
                
                save_path.write_text(
                    json.dumps(model_dict, indent=2),
                    encoding="utf-8"
                )
                logger.info(f"Model saved to {save_path}")
                
            except Exception as e:
                logger.error(f"Error saving model: {e}")
    
    @classmethod
    def load(cls, path: Optional[pathlib.Path] = None):
        """
        Load model from disk or create new if not exists.
        
        Args:
            path: Optional custom path (defaults to MODEL_PATH)
            
        Returns:
            ResearchModel instance
        """
        load_path = path or MODEL_PATH
        model = cls()
        
        if load_path.exists():
            try:
                with LOCK:
                    model_dict = json.loads(load_path.read_text(encoding="utf-8"))
                    
                    # Extract metadata if present
                    meta = model_dict.pop("_meta", {})
                    model.n_samples = meta.get("n_samples", 0)
                    
                    # Load pipeline
                    model.clf = model.clf.from_dict(model_dict)
                    
                logger.info(f"Model loaded from {load_path} ({model.n_samples} samples)")
                
            except Exception as e:
                logger.error(f"Error loading model: {e}, using fresh model")
        else:
            logger.info("No saved model found, using fresh model")
        
        return model
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current model metrics.

        Returns:
            Dict with metrics
        """
        with LOCK:
            return {
                "n_samples": self.n_samples,
                "log_loss": self.log_loss.get() if self.n_samples > 0 else None,
                "model_version": "rsm-v1"
            }


# Global model instance
MODEL = ResearchModel.load()


def predict_proba(x: Dict[str, Any]) -> float:
    """
    Convenience function for prediction.
    
    Args:
        x: Feature dict
        
    Returns:
        Probability of positive 3-day return
    """
    return MODEL.predict_proba(x)


def learn_and_save(x: Dict[str, Any], y: int):
    """
    Convenience function for training and persistence.
    
    Args:
        x: Feature dict
        y: Label (0 or 1)
    """
    MODEL.learn_one(x, y)
    MODEL.save()


def get_metrics() -> Dict[str, Any]:
    """
    Get current model metrics.
    
    Returns:
        Dict with metrics
    """
    return MODEL.get_metrics()

