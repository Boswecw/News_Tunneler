"""Price cache model for storing fetched price data."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from app.models.base import Base


class PriceCache(Base):
    """Model for caching price data from external APIs."""
    
    __tablename__ = "prices_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    vendor = Column(String, nullable=False)  # alphavantage, finnhub, yahoo
    data_type = Column(String, nullable=False)  # daily, intraday
    payload_json = Column(Text, nullable=False)  # JSON string of price data
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Composite index for efficient lookups
    __table_args__ = (
        Index('ix_ticker_vendor_type', 'ticker', 'vendor', 'data_type'),
    )

