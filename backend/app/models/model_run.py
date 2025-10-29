"""ModelRun model for tracking ML training runs."""
from sqlalchemy import Column, Integer, String, JSON
from app.models.base import Base, TimestampMixin


class ModelRun(Base, TimestampMixin):
    """
    ML model training run record.
    
    Attributes:
        id: Primary key
        version: Model version (e.g., "v20251028")
        weights: JSON dict of feature weights
        metrics: JSON dict of training metrics (accuracy, etc.)
    """
    __tablename__ = "model_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, nullable=False, unique=True, index=True)
    weights = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=False)

