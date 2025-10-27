"""Webhook model for notifications."""
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .base import Base, TimestampMixin


class WebhookType(str, Enum):
    """Enum for webhook types."""
    SLACK = "slack"
    EMAIL = "email"


class Webhook(Base, TimestampMixin):
    """Model for notification webhooks."""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    webhook_type = Column(String, nullable=False)
    target = Column(String, nullable=False)  # URL for Slack, email for Email
    enabled = Column(Boolean, default=True, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Webhook(type={self.webhook_type}, target={self.target})>"

