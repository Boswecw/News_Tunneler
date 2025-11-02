"""
Report Builder Service

Builds daily opportunities email reports by:
1. Fetching latest predictions from opportunities_cache
2. Enriching with technical indicators from signals
3. Applying filters and ranking by composite score
4. Building template context for email rendering
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from zoneinfo import ZoneInfo

from app.core.db import get_db_context
from app.core.logging import logger
from app.core.config import get_settings
from app.models import OpportunityCache, Signal, Article
import json


def compute_composite_score(
    confidence: float,
    expected_return_pct: float,
    r2_score: float
) -> float:
    """
    Compute composite opportunity score.
    
    Formula: 40% confidence + 40% |return| magnitude + 20% R²
    (normalize return with /10 to keep in 0-1 range)
    
    Args:
        confidence: ML/LLM confidence (0..1)
        expected_return_pct: Expected return percentage
        r2_score: Model R² score (0..1)
    
    Returns:
        Composite score (0..1+ range)
    """
    return (0.4 * confidence) + (0.4 * abs(expected_return_pct) / 10.0) + (0.2 * r2_score)


def fetch_latest_opportunities(db: Session, since_hours: int = 24) -> List[Dict]:
    """
    Fetch latest opportunities from cache.
    
    Args:
        db: Database session
        since_hours: Look back window in hours
    
    Returns:
        List of opportunity dicts
    """
    cutoff = datetime.utcnow() - timedelta(hours=since_hours)
    
    opportunities = (
        db.query(OpportunityCache)
        .filter(
            OpportunityCache.cached_at >= cutoff,
            OpportunityCache.expires_at > datetime.utcnow()
        )
        .order_by(OpportunityCache.composite_score.desc())
        .all()
    )
    
    logger.info(f"Fetched {len(opportunities)} opportunities from cache (last {since_hours}h)")
    
    return [opp.to_dict() for opp in opportunities]


def enrich_with_indicators(opportunities: List[Dict], db: Session) -> List[Dict]:
    """
    Enrich opportunities with latest technical indicators from signals.
    
    Args:
        opportunities: List of opportunity dicts
        db: Database session
    
    Returns:
        Enriched opportunities with indicators
    """
    enriched = []
    
    for opp in opportunities:
        symbol = opp["symbol"]
        
        # Get latest signal for this symbol
        latest_signal = (
            db.query(Signal)
            .filter(Signal.symbol == symbol)
            .order_by(desc(Signal.created_at))
            .first()
        )
        
        if latest_signal and latest_signal.features:
            features = latest_signal.features
            
            # Add technical indicators
            opp["rsi"] = features.get("rsi14")
            opp["sma20"] = features.get("sma20")
            opp["sma50"] = features.get("sma50")
            opp["current_price"] = features.get("adj_close")
            opp["volume_spike_x"] = features.get("volume_spike_x", 1.0)
            opp["vwap_gap_pct"] = features.get("vwap_dev", 0.0) * 100  # Convert to %
            
            # Determine trend
            if opp["sma20"] and opp["sma50"]:
                opp["trend"] = "Above SMA50" if opp["sma20"] > opp["sma50"] else "Below SMA50"
            else:
                opp["trend"] = "Unknown"
            
            enriched.append(opp)
        else:
            logger.warning(f"No signal data found for {symbol}, skipping")
    
    logger.info(f"Enriched {len(enriched)}/{len(opportunities)} opportunities with indicators")
    return enriched


def apply_filters(
    opportunities: List[Dict],
    min_confidence: float = 0.70,
    min_expected_return_pct: float = 1.0,
    min_r2: float = 0.95
) -> Tuple[List[Dict], List[Dict]]:
    """
    Apply filters and split into buy/sell buckets.
    
    Args:
        opportunities: List of enriched opportunities
        min_confidence: Minimum confidence threshold
        min_expected_return_pct: Minimum absolute expected return %
        min_r2: Minimum R² score
    
    Returns:
        Tuple of (buys, sells) lists, sorted by composite_score desc
    """
    settings = get_settings()
    max_per_side = getattr(settings, 'report_max_tickers_per_side', 8)
    
    buys = []
    sells = []
    
    for opp in opportunities:
        # Apply filters
        confidence = opp.get("llm_confidence") or opp.get("ml_confidence") or 0.0
        r2_score = opp.get("model_r2") or 0.0
        
        # Skip if missing indicators
        if opp.get("rsi") is None:
            continue
        
        # Skip if below thresholds
        if confidence < min_confidence:
            continue
        if r2_score < min_r2:
            continue
        
        # Infer expected return from stance or composite score
        # (In real system, this would come from prediction model)
        stance = opp.get("llm_stance", "NEUTRAL")
        expected_return = 0.0
        
        if stance == "BULLISH":
            expected_return = confidence * 5.0  # Estimate: 0-5% return
        elif stance == "BEARISH":
            expected_return = -confidence * 5.0  # Estimate: 0-5% loss
        
        # Skip if return too small
        if abs(expected_return) < min_expected_return_pct:
            continue
        
        # Add expected return and recompute composite score
        opp["expected_return_pct"] = expected_return
        opp["composite_score"] = compute_composite_score(confidence, expected_return, r2_score)
        
        # Bucket by direction
        if expected_return > 0:
            buys.append(opp)
        else:
            sells.append(opp)
    
    # Sort and limit
    buys = sorted(buys, key=lambda x: x["composite_score"], reverse=True)[:max_per_side]
    sells = sorted(sells, key=lambda x: x["composite_score"], reverse=True)[:max_per_side]
    
    logger.info(f"Filtered to {len(buys)} buys and {len(sells)} sells")
    return buys, sells


def build_market_snapshot(opportunities: List[Dict]) -> Dict:
    """
    Build market snapshot summary.
    
    Args:
        opportunities: All opportunities (before filtering)
    
    Returns:
        Dict with market_mood, notable_catalysts, confidence_range
    """
    if not opportunities:
        return {
            "market_mood": "Neutral",
            "notable_catalysts": [],
            "confidence_range": "N/A",
        }
    
    # Calculate market mood from stances
    stance_map = {"BULLISH": 1, "BEARISH": -1, "NEUTRAL": 0}
    stances = [stance_map.get(opp.get("llm_stance", "NEUTRAL"), 0) for opp in opportunities]
    avg_stance = sum(stances) / len(stances) if stances else 0
    
    if avg_stance > 0.2:
        mood = "Bullish"
    elif avg_stance < -0.2:
        mood = "Bearish"
    else:
        mood = "Neutral"
    
    # Extract notable catalysts (from article titles)
    catalysts = []
    for opp in opportunities[:10]:  # Top 10
        title = opp.get("article_title", "")
        if title and len(title) > 20:
            catalysts.append(title[:80])
    
    # Get unique catalysts (limit to 5)
    unique_catalysts = list(dict.fromkeys(catalysts))[:5]
    
    # Confidence range
    confidences = [
        opp.get("llm_confidence") or opp.get("ml_confidence") or 0.0
        for opp in opportunities
    ]
    if confidences:
        min_conf = min(confidences)
        max_conf = max(confidences)
        conf_range = f"{min_conf:.0%}–{max_conf:.0%}"
    else:
        conf_range = "N/A"
    
    return {
        "market_mood": mood,
        "notable_catalysts": unique_catalysts,
        "confidence_range": conf_range,
    }


def build_report_context(session_label: str = "Pre-Market") -> Dict:
    """
    Build complete report context for email templates.
    
    Args:
        session_label: Trading session label (Pre-Market, Mid-Day, After-Close)
    
    Returns:
        Dict with all template variables
    """
    settings = get_settings()
    
    with get_db_context() as db:
        # Fetch opportunities
        opportunities = fetch_latest_opportunities(db, since_hours=24)
        
        # Enrich with indicators
        enriched = enrich_with_indicators(opportunities, db)
        
        # Apply filters and split
        buys, sells = apply_filters(
            enriched,
            min_confidence=getattr(settings, 'report_min_confidence', 0.70),
            min_expected_return_pct=getattr(settings, 'report_min_expected_return_pct', 1.0),
            min_r2=getattr(settings, 'report_min_r2', 0.95),
        )
        
        # Build snapshot
        snapshot = build_market_snapshot(enriched)
    
    # Build context
    et_tz = ZoneInfo("America/New_York")
    now_et = datetime.now(et_tz)
    
    context = {
        "session_label": session_label,
        "report_date": now_et.strftime("%B %d, %Y"),
        "report_time": now_et.strftime("%I:%M %p ET"),
        "buys": buys,
        "sells": sells,
        "total_candidates": len(buys) + len(sells),
        "market_snapshot": snapshot,
        "backtest_summary": None,  # TODO: Implement if backtest_stats table exists
    }
    
    logger.info(f"Built report context: {len(buys)} buys, {len(sells)} sells")
    return context

