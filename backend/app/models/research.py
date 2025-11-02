"""Research model database tables for self-training ML pipeline."""
from sqlalchemy import Column, String, Float, Integer, Text
from app.models.base import Base


class ResearchFeatures(Base):
    """
    Frozen feature snapshot captured at article publish time.
    Guarantees no look-ahead bias for training.
    """
    __tablename__ = "research_features"
    
    article_id = Column(String, primary_key=True)
    symbol = Column(String, index=True, nullable=False)
    published_at = Column(String, index=True, nullable=False)  # ISO8601
    features_json = Column(Text, nullable=False)  # JSON snapshot of all features
    created_at = Column(String, nullable=False)  # ISO8601


class ResearchLabels(Base):
    """
    Auto-generated labels from realized market returns.
    Created N trading days after publish to allow outcome measurement.
    """
    __tablename__ = "research_labels"
    
    article_id = Column(String, primary_key=True)
    label = Column(Integer, nullable=False)  # 0 or 1 (binary classification)
    ret_3d = Column(Float, nullable=False)  # Actual 3-day return
    threshold = Column(Float, nullable=False)  # Threshold used for labeling
    entry_day = Column(String, nullable=False)  # ISO8601 date of entry
    created_at = Column(String, nullable=False)  # ISO8601

