"""API routes for price analysis and technical indicators."""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
import pandas as pd
from app.core.prices import get_daily_prices, compute_indicators, compute_gap_percent
from app.core.event_study import get_typical_reaction
from app.core.logging import logger

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/summary/{ticker}")
def get_summary(ticker: str):
    """
    Get current price summary with technical indicators.
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, NVDA)
    
    Returns:
        JSON with current price, SMA20/50, RSI14, ATR14, 52-week stats, volume
    """
    try:
        ticker = ticker.upper()
        logger.info(f"Fetching summary for {ticker}")
        
        # Get price data
        df = get_daily_prices(ticker)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No price data found for {ticker}")
        
        # Compute indicators
        df = compute_indicators(df)
        
        # Get most recent data
        last = df.iloc[-1]
        
        # Build response
        summary = {
            "ticker": ticker,
            "date": str(last["date"].date()) if pd.notna(last["date"]) else None,
            "price": round(float(last["adj_close"]), 4) if pd.notna(last["adj_close"]) else None,
            "open": round(float(last["open"]), 4) if pd.notna(last["open"]) else None,
            "high": round(float(last["high"]), 4) if pd.notna(last["high"]) else None,
            "low": round(float(last["low"]), 4) if pd.notna(last["low"]) else None,
            "volume": int(last["volume"]) if pd.notna(last["volume"]) else None,
            "sma20": round(float(last["sma20"]), 4) if pd.notna(last["sma20"]) else None,
            "sma50": round(float(last["sma50"]), 4) if pd.notna(last["sma50"]) else None,
            "rsi14": round(float(last["rsi14"]), 2) if pd.notna(last["rsi14"]) else None,
            "atr14": round(float(last["atr14"]), 4) if pd.notna(last["atr14"]) else None,
            "from_52w_high_%": round(float(last["from_52w_high_%"]), 2) if pd.notna(last["from_52w_high_%"]) else None,
            "from_52w_low_%": round(float(last["from_52w_low_%"]), 2) if pd.notna(last["from_52w_low_%"]) else None,
            "volume_vs_avg_%": round(float(last["volume_vs_avg_%"]), 2) if pd.notna(last["volume_vs_avg_%"]) else None,
        }
        
        # Add interpretation flags
        flags = []
        
        if summary["rsi14"] is not None:
            if summary["rsi14"] < 30:
                flags.append("oversold_zone")
            elif summary["rsi14"] > 70:
                flags.append("overbought_zone")
        
        if summary["price"] and summary["sma20"] and summary["sma50"]:
            if summary["price"] > summary["sma20"] and summary["price"] > summary["sma50"]:
                flags.append("uptrend_intact")
            elif summary["price"] < summary["sma20"] and summary["price"] < summary["sma50"]:
                flags.append("downtrend_intact")
        
        if summary["from_52w_high_%"] is not None and summary["from_52w_high_%"] > -5:
            flags.append("near_52w_high")
        
        if summary["from_52w_low_%"] is not None and summary["from_52w_low_%"] < 5:
            flags.append("near_52w_low")
        
        if summary["volume_vs_avg_%"] is not None and summary["volume_vs_avg_%"] > 50:
            flags.append("unusual_volume")
        
        summary["flags"] = flags
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching summary for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")


@router.get("/event/{ticker}")
def get_event_reaction(
    ticker: str,
    event_date: str = Query(..., description="Event date in YYYY-MM-DD format")
):
    """
    Get typical stock reaction after a news event.
    
    Args:
        ticker: Stock ticker symbol
        event_date: Date of the news event (YYYY-MM-DD)
    
    Returns:
        JSON with forward returns (1d, 3d, 5d) and gap percentage
    """
    try:
        ticker = ticker.upper()
        logger.info(f"Fetching event reaction for {ticker} on {event_date}")
        
        # Parse date
        try:
            event_dt = datetime.fromisoformat(event_date)
            event_ts = pd.Timestamp(event_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get price data
        df = get_daily_prices(ticker)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No price data found for {ticker}")
        
        # Calculate forward returns
        returns = get_typical_reaction(df, event_ts, windows=(1, 3, 5))
        
        # Calculate gap percentage
        gap_pct = compute_gap_percent(df, event_ts)
        
        response = {
            "ticker": ticker,
            "event_date": event_date,
            "gap_%": round(gap_pct, 2) if gap_pct is not None else None,
            **{k: round(v, 2) if v is not None else None for k, v in returns.items()}
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event reaction for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch event reaction: {str(e)}")


@router.get("/health")
def health_check():
    """Health check endpoint for analysis service."""
    return {"status": "ok", "service": "analysis"}

