"""MLModel model for tracking trained ML models."""
from sqlalchemy import Column, Integer, String, JSON, Boolean
from app.models.base import Base, TimestampMixin


class MLModel(Base, TimestampMixin):
    """
    ML model record for tracking trained models.
    
    Attributes:
        id: Primary key
        version: Model version (e.g., "v20251028_xgboost")
        model_type: Type of model (random_forest, xgboost, lightgbm, gradient_boosting)
        model_path: Path to saved model file
        metrics: JSON dict of evaluation metrics (accuracy, precision, recall, f1, roc_auc)
        feature_importance: JSON dict of feature importance scores
        hyperparameters: JSON dict of model hyperparameters
        training_samples: Number of samples used for training
        is_active: Whether this is the active model for predictions
    """
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, nullable=False, unique=True, index=True)
    model_type = Column(String, nullable=False, index=True)
    model_path = Column(String, nullable=False)
    metrics = Column(JSON, nullable=False)
    feature_importance = Column(JSON, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    training_samples = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=False, index=True)

