"""
Signals API Endpoints

Provides ticker-level trading signals with scores and explainability.
"""
from fastapi import APIRouter, HTTPException, Body, Request
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import desc
from app.core.db import get_db_context
from app.models import Article, Score, Signal
from app.services.ticker_identifier import resolve_tickers, get_symbol_info
from app.services.scoring import strong_score, extract_news_features
from app.core.prices import get_daily_prices
from app.core.logging import logger
from app.core.market_hours import is_market_hours
from app.middleware.rate_limit import limiter
from app.core.cache import cache_result
from app.ml.signal_scoring import score_signal_with_ml, get_ml_status
from zoneinfo import ZoneInfo
import pandas as pd
import yfinance as yf
import math


router = APIRouter(prefix="/api/signals", tags=["signals"])


# In-memory signal cache (move to Redis/DB for production)
SIGNAL_CACHE: Dict[str, Dict] = {}


@cache_result(ttl=300, key_prefix="market_features")  # Cache for 5 minutes
def calculate_market_features(symbol: str) -> Dict:
    """
    Calculate market/tape features for a symbol.

    Returns dict with ret_1d, vol_z, gap_pct, atr_pct, vwap_dev, beta

    Cached for 5 minutes to reduce computation.
    """
    try:
        # Get price data
        df = get_daily_prices(symbol, days=30)
        
        if df.empty or len(df) < 2:
            logger.warning(f"Insufficient price data for {symbol}")
            return {
                "ret_1d": 0.0,
                "ret_5d": 0.0,
                "vol_z": 0.0,
                "gap_pct": 0.0,
                "atr_pct": 0.03,
                "vwap_dev": 0.0,
                "beta": 1.0,
            }
        
        # Calculate returns
        ret_1d = (df.iloc[-1]["close"] / df.iloc[-2]["close"] - 1) if len(df) >= 2 else 0.0
        ret_5d = (df.iloc[-1]["close"] / df.iloc[-6]["close"] - 1) if len(df) >= 6 else 0.0
        
        # Volume Z-score
        if "volume" in df.columns and len(df) >= 20:
            vol_mean = df["volume"].iloc[-21:-1].mean()
            vol_std = df["volume"].iloc[-21:-1].std()
            vol_z = (df.iloc[-1]["volume"] - vol_mean) / vol_std if vol_std > 0 else 0.0
        else:
            vol_z = 0.0
        
        # Gap % (today open vs prior close)
        if "open" in df.columns and len(df) >= 2:
            gap_pct = (df.iloc[-1]["open"] / df.iloc[-2]["close"] - 1)
        else:
            gap_pct = 0.0
        
        # ATR % (14-period)
        if len(df) >= 14:
            high_low = df["high"] - df["low"]
            high_close = abs(df["high"] - df["close"].shift(1))
            low_close = abs(df["low"] - df["close"].shift(1))
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.iloc[-14:].mean()
            atr_pct = atr / df.iloc[-1]["close"]
        else:
            atr_pct = 0.03
        
        # VWAP deviation (simplified: use close vs average of day)
        if "high" in df.columns and "low" in df.columns:
            vwap_proxy = (df.iloc[-1]["high"] + df.iloc[-1]["low"] + df.iloc[-1]["close"]) / 3
            vwap_dev = (df.iloc[-1]["close"] / vwap_proxy - 1)
        else:
            vwap_dev = 0.0
        
        # Beta (simplified: correlation with SPY, default to 1.0 for now)
        beta = 1.0
        
        return {
            "ret_1d": float(ret_1d),
            "ret_5d": float(ret_5d),
            "vol_z": float(vol_z),
            "gap_pct": float(gap_pct),
            "atr_pct": float(atr_pct),
            "vwap_dev": float(vwap_dev),
            "beta": beta,
        }
    
    except Exception as e:
        logger.error(f"Error calculating market features for {symbol}: {e}")
        return {
            "ret_1d": 0.0,
            "ret_5d": 0.0,
            "vol_z": 0.0,
            "gap_pct": 0.0,
            "atr_pct": 0.03,
            "vwap_dev": 0.0,
            "beta": 1.0,
        }


@router.post("/ingest/article")
def ingest_article(payload: Dict = Body(...)):
    """
    Ingest an article and generate ticker signals.
    
    Expects:
    {
        "article_id": int,
        "title": str,
        "summary": str,
        "full_text": str (optional),
        "llm_plan": dict (optional)
    }
    
    Returns:
    {
        "ok": bool,
        "signals": List[Dict],
        "count": int
    }
    """
    try:
        article_id = payload.get("article_id")
        title = payload.get("title", "")
        summary = payload.get("summary", "")
        full_text = payload.get("full_text", "")
        llm_plan = payload.get("llm_plan")
        
        # Resolve tickers
        ticker_matches = resolve_tickers(title, summary, full_text)
        
        if not ticker_matches:
            logger.info(f"No tickers resolved for article {article_id}")
            return {"ok": True, "signals": [], "count": 0}
        
        signals = []
        
        for match in ticker_matches:
            symbol = match["symbol"]
            
            # Extract news features
            news_features = extract_news_features(
                {"title": title, "summary": summary, "source_name": payload.get("source_name", "")},
                llm_plan
            )
            
            # Calculate market features
            market_features = calculate_market_features(symbol)
            
            # Combine features
            all_features = {**news_features, **market_features}
            
            # Add calendar features (placeholder for now)
            all_features["earnings_in_days"] = 999  # TODO: integrate earnings calendar
            all_features["sector_momo_pct"] = 0.5   # TODO: integrate sector data
            
            # Calculate base score
            score_result = strong_score(all_features)

            # Enhance with ML (if enabled)
            ml_result = score_signal_with_ml(
                symbol=symbol,
                base_features=all_features,
                base_score=score_result["score"],
                base_label=score_result["label"],
                use_feature_engineering=True,
                ml_weight=0.3
            )

            # Build signal
            signal = {
                "symbol": symbol,
                "article_id": article_id,
                "confidence": match["confidence"],
                "match_type": match["match_type"],
                "features": ml_result.get("features", all_features),
                "score": ml_result["score"],
                "label": ml_result["label"],
                "reasons": score_result["reasons"],
                "timestamp": score_result["timestamp"],
                "ml_metadata": {
                    "ml_enabled": ml_result.get("ml_enabled", False),
                    "ml_prediction": ml_result.get("ml_prediction"),
                    "ml_probability": ml_result.get("ml_probability"),
                    "ml_boost": ml_result.get("ml_boost", 0.0),
                    "base_score": ml_result.get("base_score", score_result["score"]),
                    "base_label": ml_result.get("base_label", score_result["label"]),
                }
            }
            
            signals.append(signal)
            
            # Cache the signal (keep latest per symbol)
            SIGNAL_CACHE[symbol] = signal
        
        logger.info(f"Generated {len(signals)} signals for article {article_id}")
        
        return {"ok": True, "signals": signals, "count": len(signals)}
    
    except Exception as e:
        logger.error(f"Error ingesting article: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
def get_top_signals(request: Request, limit: int = 20, min_score: float = 0.0):
    """
    Get top signals sorted by score.
    
    Query params:
        - limit: max number of results (default: 20)
        - min_score: minimum score threshold (default: 0.0)
    
    Returns:
        List[Dict] of signals sorted by score descending
    """
    try:
        # Filter and sort signals
        filtered = [
            sig for sig in SIGNAL_CACHE.values()
            if sig["score"] >= min_score
        ]
        
        sorted_signals = sorted(filtered, key=lambda x: x["score"], reverse=True)[:limit]
        
        return sorted_signals
    
    except Exception as e:
        logger.error(f"Error getting top signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickers/{symbol}/score")
def get_ticker_score(symbol: str):
    """
    Get latest score for a specific ticker.
    
    Returns:
        Dict with score, label, reasons, features, etc.
    """
    symbol = symbol.upper()
    
    if symbol not in SIGNAL_CACHE:
        raise HTTPException(status_code=404, detail=f"No signal found for {symbol}")
    
    return SIGNAL_CACHE[symbol]


@router.get("/tickers/{symbol}/info")
def get_ticker_info(symbol: str):
    """
    Get ticker information from symbol map.
    
    Returns:
        Dict with name, aliases, brands, exchange, country
    """
    symbol = symbol.upper()
    info = get_symbol_info(symbol)
    
    if not info:
        raise HTTPException(status_code=404, detail=f"Ticker {symbol} not found in symbol map")
    
    return info


@router.post("/recalculate/{symbol}")
def recalculate_signal(symbol: str):
    """
    Recalculate signal for a ticker using latest market data.
    
    Useful for refreshing signals without new articles.
    """
    symbol = symbol.upper()
    
    if symbol not in SIGNAL_CACHE:
        raise HTTPException(status_code=404, detail=f"No signal found for {symbol}")
    
    try:
        # Get existing signal
        old_signal = SIGNAL_CACHE[symbol]
        
        # Recalculate market features
        market_features = calculate_market_features(symbol)
        
        # Merge with existing news features
        news_features = {
            k: v for k, v in old_signal["features"].items()
            if k in ["sentiment", "magnitude", "novelty", "credibility", "topic"]
        }
        
        all_features = {**news_features, **market_features}
        all_features["earnings_in_days"] = old_signal["features"].get("earnings_in_days", 999)
        all_features["sector_momo_pct"] = old_signal["features"].get("sector_momo_pct", 0.5)
        
        # Recalculate score
        score_result = strong_score(all_features)
        
        # Update signal
        old_signal["features"] = all_features
        old_signal["score"] = score_result["score"]
        old_signal["label"] = score_result["label"]
        old_signal["reasons"] = score_result["reasons"]
        old_signal["timestamp"] = score_result["timestamp"]
        
        SIGNAL_CACHE[symbol] = old_signal
        
        logger.info(f"Recalculated signal for {symbol}: score={score_result['score']}")
        
        return old_signal
    
    except Exception as e:
        logger.error(f"Error recalculating signal for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
def ingest_signals(request: Request, payload: Dict = Body(...)) -> Dict:
    """
    Ingest signals and compute scores.

    Request body:
        {
            "signals": [
                {
                    "symbol": "AAPL",
                    "t": 1730132689123,  # milliseconds epoch
                    "features": {
                        "sentiment": 0.7,
                        "magnitude": 0.8,
                        ...
                    }
                }
            ]
        }

    Returns:
        {"ok": true, "count": 1}
    """
    try:
        signals_data = payload.get("signals", [])

        if not signals_data:
            raise HTTPException(status_code=400, detail="No signals provided")

        with get_db_context() as db:
            count = 0

            for sig_data in signals_data:
                symbol = sig_data.get("symbol")
                t = sig_data.get("t")
                features = sig_data.get("features", {})

                if not symbol or t is None:
                    logger.warning(f"Skipping signal with missing symbol or timestamp")
                    continue

                # Compute score
                score_result = strong_score(features)

                # Check if signal already exists
                existing = db.query(Signal).filter(
                    Signal.symbol == symbol,
                    Signal.t == t
                ).first()

                if existing:
                    # Update existing
                    existing.features = features
                    existing.score = score_result["score"]
                    existing.label = score_result["label"]
                    existing.reasons = score_result["reasons"]
                    db.add(existing)
                else:
                    # Create new
                    signal = Signal(
                        symbol=symbol,
                        t=t,
                        features=features,
                        score=score_result["score"],
                        label=score_result["label"],
                        reasons=score_result["reasons"],
                    )
                    db.add(signal)

                count += 1

            db.commit()

            logger.info(f"Ingested {count} signals")

            return {"ok": True, "count": count}

    except Exception as e:
        logger.error(f"Error ingesting signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/latest")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
def get_latest_signal(request: Request, symbol: str) -> Dict:
    """
    Get latest signal for a specific ticker from database.

    Returns:
        {
            "symbol": "AAPL",
            "t": 1730132689123,
            "score": 78.5,
            "label": "High-Conviction",
            "reasons": [...],
            "features": {...},
            "y_ret_1d": 0.023,  # if labeled
            "y_beat": 1  # if labeled
        }
    """
    symbol = symbol.upper()

    try:
        with get_db_context() as db:
            signal = db.query(Signal).filter(
                Signal.symbol == symbol
            ).order_by(desc(Signal.t)).first()

            if not signal:
                raise HTTPException(status_code=404, detail=f"No signal found for {symbol}")

            return {
                "symbol": signal.symbol,
                "t": signal.t,
                "score": signal.score,
                "label": signal.label,
                "reasons": signal.reasons,
                "features": signal.features,
                "y_ret_1d": signal.y_ret_1d,
                "y_beat": signal.y_beat,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest signal for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-predictions")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
def get_top_predictions(
    request: Request,
    limit: int = 10,
    min_score: float = 50.0,
    days: int = 30
):
    """
    Get top predicted stocks based on recent signals.

    Returns stocks with highest signal scores from the last N days,
    filtered by minimum score threshold. Uses 30 days of data by default
    to give the ML model more historical context for better predictions.

    Args:
        limit: Maximum number of stocks to return (default: 10)
        min_score: Minimum signal score threshold (default: 50.0)
        days: Look back period in days (default: 30)

    Returns:
        List of dicts with:
        {
            "symbol": "AAPL",
            "score": 75.3,
            "label": "High-Conviction",
            "t": 1234567890000,
            "article_id": 123,
            "confidence": 0.85
        }
    """
    try:
        with get_db_context() as db:
            # Calculate cutoff time (30 days back by default)
            cutoff = datetime.utcnow() - timedelta(days=days)
            cutoff_ms = int(cutoff.timestamp() * 1000)

            # Query signals from last N days with score >= min_score
            # Get the latest signal per symbol
            from sqlalchemy import func

            subquery = (
                db.query(
                    Signal.symbol,
                    func.max(Signal.t).label('max_t')
                )
                .filter(Signal.t >= cutoff_ms)
                .filter(Signal.score >= min_score)
                .group_by(Signal.symbol)
                .subquery()
            )

            signals = (
                db.query(Signal)
                .join(
                    subquery,
                    (Signal.symbol == subquery.c.symbol) & (Signal.t == subquery.c.max_t)
                )
                .order_by(desc(Signal.score))
                .limit(limit)
                .all()
            )

            results = []
            for signal in signals:
                results.append({
                    "symbol": signal.symbol,
                    "score": signal.score,
                    "label": signal.label,
                    "t": signal.t,
                    "article_id": signal.article_id,
                    "confidence": signal.confidence if hasattr(signal, 'confidence') else None,
                })

            logger.info(f"Returning {len(results)} top predictions (min_score={min_score}, days={days})")
            return results

    except Exception as e:
        logger.error(f"Error getting top predictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict-tomorrow/{symbol}")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
def predict_tomorrow_chart(request: Request, symbol: str) -> Dict[str, Any]:
    """
    Generate predicted price chart for tomorrow's trading session.

    Returns a static chart with:
    - Predicted price movement throughout the day
    - Predicted high and low points
    - Optimal buy time (predicted low)
    - Optimal sell time (predicted high)

    Args:
        symbol: Stock ticker symbol (e.g., AAPL)

    Returns:
        {
            "symbol": "AAPL",
            "prediction_date": "2025-10-29",
            "market_open": 1730203800000,  # 9:30 AM ET
            "market_close": 1730227200000,  # 4:00 PM ET
            "current_price": 227.34,
            "predicted_return": 2.5,  # percentage
            "predicted_close": 232.03,
            "data_points": [
                {"t": 1730203800000, "v": 227.34},  # 9:30 AM
                {"t": 1730205600000, "v": 228.12},  # 10:00 AM
                ...
            ],
            "predicted_high": {"t": 1730220000000, "v": 233.45, "time": "2:00 PM"},
            "predicted_low": {"t": 1730206400000, "v": 226.89, "time": "10:10 AM"},
            "buy_signal": {"t": 1730206400000, "time": "10:10 AM", "price": 226.89},
            "sell_signal": {"t": 1730220000000, "time": "2:00 PM", "price": 233.45}
        }
    """
    try:
        # Get current price
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")

        current_price = float(hist['Close'].iloc[-1])

        # Get latest signal for prediction
        predicted_return = 0.0
        signal_score = 0.0

        with get_db_context() as db:
            latest_signal = (
                db.query(Signal)
                .filter(Signal.symbol == symbol)
                .order_by(desc(Signal.t))
                .first()
            )

            if latest_signal and latest_signal.features:
                signal_score = latest_signal.score

                # Calculate predicted return based on signal score
                if signal_score >= 75:
                    predicted_return = 0.02 + (signal_score - 75) * 0.001  # 2-5%
                elif signal_score >= 60:
                    predicted_return = 0.01 + (signal_score - 60) * 0.0007  # 1-3%
                elif signal_score >= 45:
                    predicted_return = 0.005 + (signal_score - 45) * 0.0007  # 0.5-1.5%
                else:
                    predicted_return = 0.002  # Minimal move

                # Check sentiment direction
                sentiment = latest_signal.features.get("sentiment", 0.0)
                if sentiment < 0:
                    predicted_return = -predicted_return

        # Calculate tomorrow's market hours
        et_tz = ZoneInfo("America/New_York")
        now_et = datetime.now(et_tz)

        # Get next trading day (skip weekends)
        next_day = now_et + timedelta(days=1)
        while next_day.weekday() >= 5:  # Skip Saturday/Sunday
            next_day += timedelta(days=1)

        market_open = next_day.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = next_day.replace(hour=16, minute=0, second=0, microsecond=0)

        # Generate data points every 5 minutes (78 points for 6.5 hour trading day)
        data_points = []
        interval_minutes = 5
        total_minutes = 390  # 6.5 hours
        num_points = total_minutes // interval_minutes

        predicted_close = current_price * (1 + predicted_return)

        # Track high and low
        predicted_high = {"t": 0, "v": 0, "time": ""}
        predicted_low = {"t": 0, "v": float('inf'), "time": ""}

        for i in range(num_points + 1):
            minutes_elapsed = i * interval_minutes
            timestamp_dt = market_open + timedelta(minutes=minutes_elapsed)
            timestamp_ms = int(timestamp_dt.timestamp() * 1000)

            # Create realistic intraday movement
            # Use sine wave + trend + noise
            progress = i / num_points  # 0 to 1

            # Overall trend toward predicted close
            trend_price = current_price + (predicted_close - current_price) * progress

            # Add intraday volatility (sine wave pattern)
            volatility = abs(predicted_return) * 0.3  # 30% of predicted move
            intraday_wave = math.sin(progress * math.pi * 3) * volatility * current_price

            # Add some randomness
            import random
            noise = random.uniform(-0.002, 0.002) * current_price

            price = trend_price + intraday_wave + noise

            data_points.append({
                "t": timestamp_ms,
                "v": round(price, 2)
            })

            # Track high and low
            if price > predicted_high["v"]:
                predicted_high = {
                    "t": timestamp_ms,
                    "v": round(price, 2),
                    "time": timestamp_dt.strftime("%I:%M %p")
                }

            if price < predicted_low["v"]:
                predicted_low = {
                    "t": timestamp_ms,
                    "v": round(price, 2),
                    "time": timestamp_dt.strftime("%I:%M %p")
                }

        return {
            "symbol": symbol,
            "prediction_date": next_day.strftime("%Y-%m-%d"),
            "market_open": int(market_open.timestamp() * 1000),
            "market_close": int(market_close.timestamp() * 1000),
            "current_price": round(current_price, 2),
            "predicted_return": round(predicted_return * 100, 2),
            "predicted_close": round(predicted_close, 2),
            "signal_score": round(signal_score, 2),
            "data_points": data_points,
            "predicted_high": predicted_high,
            "predicted_low": predicted_low,
            "buy_signal": predicted_low,  # Buy at predicted low
            "sell_signal": predicted_high,  # Sell at predicted high
        }

    except Exception as e:
        logger.error(f"Error generating prediction chart for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml-status")
def get_ml_system_status():
    """
    Get ML system status.

    Returns information about ML models, feature engineering, and caching.
    """
    try:
        status = get_ml_status()
        return status
    except Exception as e:
        logger.error(f"Error getting ML status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
