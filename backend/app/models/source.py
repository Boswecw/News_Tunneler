"""Source model for RSS/Atom feeds and news APIs."""
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from datetime import datetime
from .base import Base, TimestampMixin


class SourceType(str, Enum):
    """Enum for source types."""
    RSS = "rss"
    ATOM = "atom"
    NEWSAPI = "newsapi"


class Source(Base, TimestampMixin):
    """Model for news sources (RSS feeds, APIs, etc.)."""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    source_type = Column(String, default=SourceType.RSS, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    last_fetched_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_source_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name={self.name}, url={self.url})>"

