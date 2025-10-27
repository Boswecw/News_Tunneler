"""Configuration management for news-tunneler backend."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Core
    env: str = "dev"
    port: int = 8000
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/news.db"

    # Polling
    poll_interval_sec: int = 900  # 15 minutes

    # Scoring
    min_alert_score: int = 12

    # Optional providers
    newsapi_key: str = ""
    alphavantage_key: str = ""

    # Notifications
    slack_webhook_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_email_to: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def slack_enabled(self) -> bool:
        return bool(self.slack_webhook_url)

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.alert_email_to)

    @property
    def newsapi_enabled(self) -> bool:
        return bool(self.newsapi_key)

    @property
    def alphavantage_enabled(self) -> bool:
        return bool(self.alphavantage_key)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

