"""
Prediction Bounds Model

Stores intraday high/low bound predictions.
"""
from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime, Index
from sqlalchemy.sql import func
from .base import Base, TimestampMixin


class PredictionBounds(Base, TimestampMixin):
    """
    Intraday price bounds predictions.
    
    Stores predicted upper/lower bounds for future price movements.
    """
    __tablename__ = "prediction_bounds"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Stock identifier
    ticker = Column(String(10), nullable=False, index=True)
    
    # Timestamp (milliseconds since epoch)
    ts = Column(BigInteger, nullable=False, index=True)
    
    # Prediction parameters
    interval = Column(String(10), nullable=False)  # '1m', '5m', etc.
    horizon = Column(Integer, nullable=False)  # Number of bars ahead
    
    # Predicted bounds
    lower = Column(Float, nullable=False)  # Lower bound (e.g., q10)
    upper = Column(Float, nullable=False)  # Upper bound (e.g., q90)
    mid = Column(Float, nullable=False)  # Midpoint
    
    # Model metadata
    model_version = Column(String(100), nullable=True)
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_ticker_ts_interval_horizon', 'ticker', 'ts', 'interval', 'horizon'),
        Index('idx_ticker_interval_horizon', 'ticker', 'interval', 'horizon'),
    )
    
    def __repr__(self):
        return f"<PredictionBounds(ticker={self.ticker}, ts={self.ts}, interval={self.interval}, horizon={self.horizon}, lower={self.lower}, upper={self.upper})>"

