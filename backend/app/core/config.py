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
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"]

    # LLM Analysis
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_min_alert_score: int = 12

    # Price Data
    use_price_source: str = "yahoo"  # Options: yahoo, polygon
    polygon_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == 'cors_origins':
                if not raw_val or raw_val.strip() == '':
                    return ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"]
                import json
                return json.loads(raw_val)
            return raw_val

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

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key != "your_key_here")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

