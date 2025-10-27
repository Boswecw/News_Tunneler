"""Setting model for user preferences."""
from sqlalchemy import Column, Integer, String, Float, JSON
from .base import Base


class Setting(Base):
    """Model for application settings (singleton)."""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    
    # Weights for scoring (0-1 scale)
    weight_catalyst = Column(Float, default=1.0, nullable=False)
    weight_novelty = Column(Float, default=1.0, nullable=False)
    weight_credibility = Column(Float, default=1.0, nullable=False)
    weight_sentiment = Column(Float, default=1.0, nullable=False)
    weight_liquidity = Column(Float, default=1.0, nullable=False)
    
    # Alert threshold
    min_alert_score = Column(Float, default=12.0, nullable=False)
    
    # Polling interval in seconds
    poll_interval_sec = Column(Integer, default=900, nullable=False)

    def __repr__(self) -> str:
        return f"<Setting(min_alert_score={self.min_alert_score})>"

