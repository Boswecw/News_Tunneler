"""
Backtest API endpoints for analyzing historical stock reactions to news events.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
import json

from app.core.db import get_db
from app.models.article import Article
from app.core.prices import get_daily_prices
from app.core.backtest import forward_returns
from app.core.logging import logger

router = APIRouter(prefix="/api/analysis")


@router.get("/backtest")
def backtest(
    ticker: str = Query(..., description="Stock ticker symbol (e.g., AAPL)"),
    catalyst: str = Query(None, description="Filter by catalyst type: EARNINGS|FDA|M&A|CONTRACT|GUIDANCE|MACRO|OTHER"),
    lookback_days: int = Query(365, description="Number of days to look back for events"),
    min_score: float = Query(0.0, description="Minimum alert score to include"),
    windows: str = Query("1,3,5", description="Comma-separated forward windows in trading days"),
    db: Session = Depends(get_db)
):
    """
    Backtest historical stock reactions to news events.
    
    Uses historical alert dates from the Articles table (filtered by ticker and optional catalyst)
    within the lookback window. Computes forward returns from end-of-day prices.
    
    Returns:
        - Aggregated statistics (avg, median, win rate) for each forward window
        - Individual event samples with their forward returns
    """
    tkr = ticker.upper()
    logger.info(f"Backtesting {tkr} with catalyst={catalyst}, lookback={lookback_days}d")
    
    # 1) Get price history
    try:
        df = get_daily_prices(tkr)
    except Exception as e:
        logger.error(f"Failed to fetch prices for {tkr}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch price data: {str(e)}")
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No price data available for {tkr}")
    
    # Ensure we have the required columns
    df = df[["date", "adj_close"]].copy()
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    
    # 2) Pull events from Articles table
    since = datetime.utcnow() - timedelta(days=lookback_days)
    
    # Build query
    q = db.query(Article).filter(
        Article.ticker_guess == tkr,
        Article.published_at >= since,
        Article.llm_plan.isnot(None)  # Only include articles with LLM analysis
    )
    
    articles = q.order_by(Article.published_at.asc()).all()
    
    if not articles:
        raise HTTPException(
            status_code=404,
            detail=f"No events found for {tkr} in the last {lookback_days} days"
        )
    
    # 3) Extract event dates matching catalyst filter (if provided)
    evts = []
    for a in articles:
        if not a.llm_plan:
            continue
        
        # Parse llm_plan JSON if it's a string
        plan = a.llm_plan
        if isinstance(plan, str):
            try:
                plan = json.loads(plan)
            except:
                continue
        
        # Filter by catalyst type if specified
        if catalyst:
            article_catalyst = plan.get("catalyst_type")
            if article_catalyst != catalyst:
                continue
        
        # Check minimum score if specified
        if min_score > 0:
            # Get the score from the scores relationship
            if hasattr(a, 'score') and a.score:
                if a.score.total < min_score:
                    continue
        
        # Use the publish date as event date (remove timezone if present)
        if a.published_at:
            # Convert to pandas Timestamp and remove timezone info
            ts = pd.Timestamp(a.published_at)
            if ts.tz is not None:
                ts = ts.tz_localize(None)
            evts.append(ts.date())
    
    if not evts:
        catalyst_msg = f" with catalyst={catalyst}" if catalyst else ""
        raise HTTPException(
            status_code=404,
            detail=f"No matching events{catalyst_msg} for {tkr} in the lookback window"
        )
    
    logger.info(f"Found {len(evts)} events for {tkr}")
    
    # 4) Parse windows parameter
    try:
        win_list = tuple(int(x.strip()) for x in windows.split(",") if x.strip().isdigit())
        if not win_list:
            win_list = (1, 3, 5)
    except:
        win_list = (1, 3, 5)
    
    # 5) Compute forward returns
    try:
        res = forward_returns(df, evts, win_list)
    except Exception as e:
        logger.error(f"Failed to compute forward returns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compute returns: {str(e)}")
    
    return {
        "ticker": tkr,
        "catalyst": catalyst or "ANY",
        "events_count": len(res["samples"]),
        "lookback_days": lookback_days,
        **res
    }


@router.get("/backtest/health")
def backtest_health():
    """Health check for backtest endpoint."""
    return {"status": "ok", "service": "backtest"}

