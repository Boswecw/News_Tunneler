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

    # PostgreSQL (Phase 2 Improvement)
    use_postgresql: bool = False
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "news_tunneler"
    postgres_user: str = "news_tunneler"
    postgres_password: str = "news_tunneler_dev_password"
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20

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

    # Redis Cache (Phase 1 Improvement)
    redis_enabled: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Daily Opportunities Report
    report_recipients: list[str] = []  # Email addresses for daily report
    report_min_confidence: float = 0.70  # Minimum confidence threshold
    report_min_expected_return_pct: float = 1.0  # Minimum expected return %
    report_min_r2: float = 0.95  # Minimum R² score
    report_max_tickers_per_side: int = 8  # Max tickers per buy/sell side
    enable_report_pdf: bool = False  # Enable PDF attachment (requires WeasyPrint)
    admin_token: str = ""  # Admin token for manual report triggers

    # Intraday Bounds Prediction
    intraday_interval: str = "1m"  # Data interval for intraday predictions
    intraday_horizons: str = "5,15"  # Comma-separated prediction horizons
    bounds_quantiles: str = "0.1,0.9"  # Comma-separated quantiles
    predict_store_db: bool = False  # Whether to store predictions in database

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
            if field_name == 'report_recipients':
                if not raw_val or raw_val.strip() == '':
                    return []
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

    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL based on use_postgresql flag."""
        if self.use_postgresql:
            return self.postgres_url
        return self.database_url

    @property
    def report_enabled(self) -> bool:
        """Check if daily report is enabled (has recipients and email configured)."""
        return bool(self.report_recipients and self.email_enabled)

    @property
    def intraday_horizons_list(self) -> list[int]:
        """Parse intraday_horizons string to list of integers."""
        return [int(h.strip()) for h in self.intraday_horizons.split(',') if h.strip()]

    @property
    def bounds_quantiles_list(self) -> list[float]:
        """Parse bounds_quantiles string to list of floats."""
        return [float(q.strip()) for q in self.bounds_quantiles.split(',') if q.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

