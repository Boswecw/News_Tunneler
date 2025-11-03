"""Article model for news articles."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base, TimestampMixin

# Use JSON for SQLite and JSONB for PostgreSQL so we can leverage
# native jsonb indexes in production while keeping local compatibility.
JSONType = JSON().with_variant(JSONB, "postgresql")


class Article(Base, TimestampMixin):
    """Model for news articles."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False, index=True)
    ticker_guess = Column(String, nullable=True, index=True)

    # LLM analysis fields
    llm_plan = Column(JSONType, nullable=True)  # Full JSON from LLM
    strategy_bucket = Column(String, nullable=True)  # Mapped strategy label
    strategy_risk = Column(JSONType, nullable=True)  # Risk parameters

    __table_args__ = (
        Index("idx_article_published_at", "published_at"),
        Index("idx_article_ticker_guess", "ticker_guess"),
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title={self.title[:50]}...)>"
