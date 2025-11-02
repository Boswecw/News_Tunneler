"""
Opportunity cache model for persisting top opportunities across restarts.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.models.base import Base


class OpportunityCache(Base):
    """
    Stores cached opportunities data with TTL.
    
    This table persists the top opportunities across backend restarts,
    ensuring users don't lose their opportunities list when the system
    restarts or when they reload the page.
    """
    __tablename__ = "opportunities_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    composite_score = Column(Float, nullable=False, index=True)
    signal_score = Column(Float, nullable=True)
    llm_confidence = Column(Float, nullable=True)
    llm_stance = Column(String(20), nullable=True)
    ml_confidence = Column(Float, nullable=True)
    model_r2 = Column(Float, nullable=True)
    model_trained = Column(Boolean, nullable=True)
    model_mode = Column(String(10), nullable=True)
    article_id = Column(Integer, nullable=True)
    article_title = Column(String(500), nullable=True)
    signal_timestamp = Column(Float, nullable=True)
    cached_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    def to_dict(self):
        """Convert to dictionary matching API response format."""
        return {
            "symbol": self.symbol,
            "composite_score": self.composite_score,
            "signal_score": self.signal_score,
            "llm_confidence": self.llm_confidence,
            "llm_stance": self.llm_stance,
            "ml_confidence": self.ml_confidence,
            "model_r2": self.model_r2,
            "model_trained": self.model_trained,
            "model_mode": self.model_mode,
            "article_id": self.article_id,
            "article_title": self.article_title,
            "signal_timestamp": self.signal_timestamp,
        }

