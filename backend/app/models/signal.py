"""Signal model for storing trading signals."""
from sqlalchemy import Column, Integer, String, Float, BigInteger, JSON, Index
from app.models.base import Base, TimestampMixin


class Signal(Base, TimestampMixin):
    """
    Trading signal with features, score, and forward return labels.

    Attributes:
        id: Primary key
        symbol: Ticker symbol (e.g., "AAPL")
        article_id: Foreign key to article that generated this signal
        t: Timestamp in milliseconds (epoch)
        features: JSON dict of all input features
        score: Computed score (0-100)
        label: Signal label (High-Conviction, Opportunity, Watch, Ignore)
        reasons: JSON list of score breakdown items
        confidence: LLM confidence score (0.0-1.0)
        y_ret_1d: 1-day forward return (for training)
        y_beat: 1 if beat index, 0 otherwise (for training)
    """
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    article_id = Column(Integer, nullable=True, index=True)  # Link to source article
    t = Column(BigInteger, nullable=False, index=True)  # milliseconds epoch
    features = Column(JSON, nullable=False)
    score = Column(Float, nullable=False, index=True)
    label = Column(String, nullable=False)
    reasons = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)  # LLM confidence (0.0-1.0)
    y_ret_1d = Column(Float, nullable=True)  # Forward return for training
    y_beat = Column(Integer, nullable=True)  # 1 if beat index, 0 otherwise

    __table_args__ = (
        Index('idx_symbol_t', 'symbol', 't', unique=True),
    )

