"""
Intraday Bounds Prediction API

Provides endpoints for predicting intraday high/low price bounds.
"""
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import desc

from app.core.db import get_db_context
from app.models.prediction_bounds import PredictionBounds
from app.middleware.rate_limit import limiter
from app.core.logging import logger

# Import ML modules
from app.ml.intraday_features import make_intraday_features
from app.ml.intraday_models import load_model

router = APIRouter(prefix="/predict/intraday-bounds", tags=["predict"])

# Model cache
_model_cache: Dict[str, tuple] = {}


# Pydantic schemas
class BoundsPoint(BaseModel):
    """Single bounds prediction point."""
    ts: int = Field(..., description="Timestamp in milliseconds")
    lower: float = Field(..., description="Lower bound price")
    upper: float = Field(..., description="Upper bound price")
    mid: float = Field(..., description="Midpoint price")
    current_price: Optional[float] = Field(None, description="Current price at this timestamp")


class BoundsResponse(BaseModel):
    """Response with bounds predictions."""
    ticker: str
    interval: str
    horizon: int
    model_version: str
    points: List[BoundsPoint]
    metadata: Dict = Field(default_factory=dict)


class BatchBoundsRequest(BaseModel):
    """Request for batch bounds prediction."""
    tickers: List[str] = Field(..., description="List of ticker symbols")
    interval: str = Field(default="1m", description="Data interval")
    horizon: int = Field(default=5, description="Prediction horizon in bars")
    limit: int = Field(default=200, description="Number of recent bars to return")


def load_recent_bars(ticker: str, interval: str, limit: int = 1000) -> pd.DataFrame:
    """
    Load recent intraday bars for a ticker.
    
    Args:
        ticker: Stock symbol
        interval: Data interval ('1m', '5m', etc.)
        limit: Number of recent bars to load
        
    Returns:
        DataFrame with OHLCV data
    """
    try:
        import yfinance as yf
        
        # Map interval to yfinance period
        if interval == '1m':
            period = '7d'
        elif interval == '5m':
            period = '60d'
        else:
            period = '60d'
        
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            raise ValueError(f"No data available for {ticker}")
        
        # Take last `limit` bars
        df = df.tail(limit)
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading bars for {ticker}: {e}")
        raise


def get_model_path(ticker: str, interval: str, horizon: int, target: str) -> Optional[Path]:
    """
    Find model file for given parameters.
    
    Args:
        ticker: Stock symbol
        interval: Data interval
        horizon: Prediction horizon
        target: 'high' or 'low'
        
    Returns:
        Path to model file or None if not found
    """
    model_dir = Path("backend/app/ml/artifacts")
    
    # Look for most recent model
    pattern = f"intraday_bounds_{ticker}_{interval}_{target}_{horizon}bars_*.joblib"
    models = list(model_dir.glob(pattern))
    
    if not models:
        return None
    
    # Return most recent
    return sorted(models)[-1]


def load_or_cache_model(ticker: str, interval: str, horizon: int, target: str):
    """Load model from cache or disk."""
    cache_key = f"{ticker}_{interval}_{horizon}_{target}"
    
    if cache_key in _model_cache:
        return _model_cache[cache_key]
    
    model_path = get_model_path(ticker, interval, horizon, target)
    if not model_path:
        raise FileNotFoundError(f"No model found for {ticker} {interval} horizon={horizon} target={target}")
    
    model, metadata = load_model(model_path)
    _model_cache[cache_key] = (model, metadata)
    
    return model, metadata


@router.get("/{ticker}", response_model=BoundsResponse)
@limiter.limit("30/minute")
async def get_bounds(
    request: Request,
    ticker: str,
    interval: str = Query(default="1m", description="Data interval"),
    horizon: int = Query(default=5, description="Prediction horizon in bars"),
    limit: int = Query(default=200, description="Number of recent predictions to return")
):
    """
    Get intraday bounds predictions for a ticker.
    
    Returns predicted upper/lower bounds for future price movements.
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL)
        interval: Data interval ('1m', '5m', '15m', '30m', '1h')
        horizon: Prediction horizon in bars (e.g., 5 means predict 5 bars ahead)
        limit: Number of recent bars to return predictions for
        
    Returns:
        BoundsResponse with predicted bounds for each timestamp
    """
    try:
        # Load recent bars
        df = load_recent_bars(ticker, interval, limit=limit + 100)  # Extra for feature calculation
        
        # Create features
        features = make_intraday_features(df, include_session_context=True)
        
        # Load models
        try:
            model_high, metadata_high = load_or_cache_model(ticker, interval, horizon, 'high')
            model_low, metadata_low = load_or_cache_model(ticker, interval, horizon, 'low')
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Models not found for {ticker}. Please train models first using: "
                       f"python -m backend.app.ml.train_intraday_bounds --ticker {ticker} --interval {interval} --horizons {horizon}"
            )
        
        # Predict
        pred_high = model_high.predict(features)
        pred_low = model_low.predict(features)
        
        # Get quantiles (assume 0.1 and 0.9)
        quantiles = sorted(pred_high.keys())
        lower_q = quantiles[0]
        upper_q = quantiles[-1]
        
        # Build response points
        points = []
        for i in range(len(features)):
            # Use upper bound from high model and lower bound from low model
            upper_bound = pred_high[upper_q][i]
            lower_bound = pred_low[lower_q][i]
            mid = (upper_bound + lower_bound) / 2
            
            ts_ms = int(df.index[i].timestamp() * 1000)
            current_price = float(df['Close'].iloc[i]) if 'Close' in df.columns else None
            
            points.append(BoundsPoint(
                ts=ts_ms,
                lower=round(lower_bound, 2),
                upper=round(upper_bound, 2),
                mid=round(mid, 2),
                current_price=round(current_price, 2) if current_price else None
            ))
        
        # Take last `limit` points
        points = points[-limit:]
        
        model_version = metadata_high.get('model_version', metadata_high.get('trained_at', 'unknown'))
        
        return BoundsResponse(
            ticker=ticker,
            interval=interval,
            horizon=horizon,
            model_version=model_version,
            points=points,
            metadata={
                'n_points': len(points),
                'quantiles': quantiles,
                'model_trained_at': metadata_high.get('trained_at'),
                'n_train_samples': metadata_high.get('n_train'),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting bounds for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[BoundsResponse])
@limiter.limit("10/minute")
async def get_bounds_batch(
    request: Request,
    batch_request: BatchBoundsRequest
):
    """
    Get bounds predictions for multiple tickers.
    
    Args:
        batch_request: Batch request with list of tickers and parameters
        
    Returns:
        List of BoundsResponse for each ticker
    """
    try:
        responses = []
        
        for ticker in batch_request.tickers:
            try:
                # Call single ticker endpoint logic
                response = await get_bounds(
                    request,
                    ticker,
                    batch_request.interval,
                    batch_request.horizon,
                    batch_request.limit
                )
                responses.append(response)
            except Exception as e:
                logger.warning(f"Failed to get bounds for {ticker}: {e}")
                # Continue with other tickers
                continue
        
        return responses
        
    except Exception as e:
        logger.error(f"Error in batch bounds prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/{ticker}", response_model=BoundsResponse)
@limiter.limit("30/minute")
async def get_bounds_from_db(
    request: Request,
    ticker: str,
    interval: str = Query(default="1m"),
    horizon: int = Query(default=5),
    limit: int = Query(default=200)
):
    """
    Get bounds predictions from database (if stored).
    
    This endpoint retrieves pre-computed predictions from the database
    instead of computing them on-the-fly.
    
    Args:
        ticker: Stock ticker symbol
        interval: Data interval
        horizon: Prediction horizon
        limit: Number of recent predictions to return
        
    Returns:
        BoundsResponse with stored predictions
    """
    try:
        with get_db_context() as db:
            # Query recent predictions
            predictions = (
                db.query(PredictionBounds)
                .filter(
                    PredictionBounds.ticker == ticker,
                    PredictionBounds.interval == interval,
                    PredictionBounds.horizon == horizon
                )
                .order_by(desc(PredictionBounds.ts))
                .limit(limit)
                .all()
            )
            
            if not predictions:
                raise HTTPException(
                    status_code=404,
                    detail=f"No stored predictions found for {ticker}"
                )
            
            # Convert to response
            points = [
                BoundsPoint(
                    ts=p.ts,
                    lower=p.lower,
                    upper=p.upper,
                    mid=p.mid
                )
                for p in reversed(predictions)  # Reverse to get chronological order
            ]
            
            return BoundsResponse(
                ticker=ticker,
                interval=interval,
                horizon=horizon,
                model_version=predictions[0].model_version or 'unknown',
                points=points,
                metadata={
                    'n_points': len(points),
                    'source': 'database',
                    'latest_ts': predictions[0].ts
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving bounds from DB for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

