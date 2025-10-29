"""Strategy mapping service for converting LLM output to trading strategies."""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def map_to_strategy(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map LLM analysis to a trading strategy bucket and risk parameters.
    
    Args:
        plan: Dictionary containing LLM analysis output
        
    Returns:
        Dictionary with 'bucket' (strategy label) and 'risk' (risk parameters)
    """
    catalyst_type = plan.get("catalyst_type", "OTHER")
    stance = plan.get("stance", "NEUTRAL")
    confidence = plan.get("confidence_0to1", 0.5)
    
    # Determine strategy bucket based on catalyst type and stance
    if catalyst_type in ("EARNINGS", "GUIDANCE"):
        if stance == "BULLISH":
            bucket = "Earnings Momentum"
        elif stance == "BEARISH":
            bucket = "Earnings Fade"
        else:
            bucket = "Earnings Watch"
    elif catalyst_type in ("FDA", "M&A", "CONTRACT"):
        bucket = f"Event-Driven: {catalyst_type}"
    elif catalyst_type == "MACRO":
        bucket = "Macro Shock"
    else:
        bucket = "General News"
    
    # Calculate risk parameters based on confidence and catalyst type
    # Base position size: 2% of account
    base_position_pct = 0.02
    
    # Adjust based on confidence (0.5-1.0 confidence maps to 1.0-2.0x multiplier)
    confidence_multiplier = 1.0 + (confidence - 0.5) * 2.0
    max_position_pct = min(base_position_pct * confidence_multiplier, 0.05)  # Cap at 5%
    
    # Determine review window
    near_term_days = int(plan.get("near_term_window_days", 3))
    review_in_days = min(5, max(1, near_term_days))
    
    # Build stop guideline based on catalyst type
    if catalyst_type in ("EARNINGS", "GUIDANCE"):
        stop_guideline = "Invalidate on earnings miss or guidance cut; stop at prior day low"
    elif catalyst_type in ("FDA", "M&A", "CONTRACT"):
        stop_guideline = "Invalidate on catalyst reversal or deal break; tight stop"
    elif catalyst_type == "MACRO":
        stop_guideline = "Invalidate on macro reversal; use sector ETF as hedge"
    else:
        stop_guideline = "Invalidate on break of prior day low or negative news"
    
    risk = {
        "max_position_pct": round(max_position_pct, 4),
        "stop_guideline": stop_guideline,
        "review_in_days": review_in_days,
        "confidence": round(confidence, 2)
    }
    
    logger.info(f"Mapped to strategy: {bucket} with {max_position_pct*100:.1f}% max position")
    
    return {
        "bucket": bucket,
        "risk": risk
    }

