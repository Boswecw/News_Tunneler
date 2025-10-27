"""Score model for article scoring."""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from datetime import datetime
from .base import Base, TimestampMixin


class Score(Base, TimestampMixin):
    """Model for article scores."""

    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, unique=True)
    catalyst = Column(Float, default=0.0, nullable=False)
    novelty = Column(Float, default=0.0, nullable=False)
    credibility = Column(Float, default=0.0, nullable=False)
    sentiment = Column(Float, default=0.0, nullable=False)
    liquidity = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False, index=True)
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_score_total", "total"),
        Index("idx_score_article_id", "article_id"),
    )

    def __repr__(self) -> str:
        return f"<Score(article_id={self.article_id}, total={self.total})>"

