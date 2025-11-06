"""
Strong Possibility Scoring Service

Blends news, market tape, and calendar features into a single score S∈[0,100].
Provides explainability via "reasons" for each score component.
"""
import os
import json
import math
from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.core.logging import logger

# Path to model weights file
MODEL_WEIGHTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "model_weights.json"
)

# Cache for loaded weights
_weights_cache = None


def load_model_weights() -> Dict[str, float]:
    """
    Load model weights from file or use defaults.

    Returns:
        Dict mapping feature names to weights
    """
    global _weights_cache

    if _weights_cache is not None:
        return _weights_cache

    # Try to load from file
    if os.path.exists(MODEL_WEIGHTS_PATH):
        try:
            with open(MODEL_WEIGHTS_PATH, "r") as f:
                weights = json.load(f)
            logger.info(f"Loaded model weights from {MODEL_WEIGHTS_PATH}")
            _weights_cache = weights
            return weights
        except Exception as e:
            logger.error(f"Error loading model weights: {e}")

    # Use defaults
    logger.info("Using default model weights")
    _weights_cache = {
        "sentiment": 24.0,
        "magnitude": 16.0,
        "novelty": 10.0,
        "credibility": 8.0,
        "ret_1d": 8.0,
        "vol_z": 10.0,
        "vwap_dev": 6.0,
        "gap_pct": 4.0,
        "sector_momo_pct": 6.0,
        "earnings_in_days": 4.0,
    }
    return _weights_cache


def clip(x: float, lo: float, hi: float) -> float:
    """Clip value to range [lo, hi]."""
    return max(lo, min(hi, x))


def strong_score(features: Dict) -> Dict:
    """
    Calculate strong possibility score with explainability.
    
    Args:
        features: Dict containing:
            News features:
                - sentiment: float [-1..1] entity-targeted sentiment
                - magnitude: float [0..1] materiality estimate
                - novelty: float [0..1] freshness vs last 24-72h
                - credibility: float [0..1] publisher quality
                - topic: str (earnings, guidance_up/down, M&A, litigation, etc.)
            
            Market/Tape features:
                - ret_1h: float (1-hour return %)
                - ret_1d: float (1-day return %)
                - ret_5d: float (5-day return %)
                - vol_z: float (volume Z-score vs 20-day avg)
                - gap_pct: float (today open vs prior close %)
                - atr_pct: float (ATR(14)/price)
                - vwap_dev: float (price vs VWAP deviation)
                - beta: float (risk context)
                - iv_rank: float [0..1] (optional, implied volatility rank)
            
            Calendar/Context features:
                - earnings_in_days: int (days until next earnings)
                - surprise_last_q: float (last quarter EPS surprise)
                - sector_momo_pct: float [0..1] (sector 5-day momentum percentile)
            
            Risk flags:
                - halted: bool (trading halted)
    
    Returns:
        {
            "score": float [0..100],
            "label": str (High-Conviction | Opportunity | Watch | Ignore),
            "reasons": List[Dict] (breakdown of score components),
            "timestamp": int (unix timestamp ms)
        }
    """
    # Load weights from file (or use defaults)
    model_weights = load_model_weights()

    # Map model weights to internal names (for backward compatibility)
    weights = {
        "news_sent": model_weights.get("sentiment", 24.0),
        "news_mag": model_weights.get("magnitude", 16.0),
        "novelty": model_weights.get("novelty", 10.0),
        "cred": model_weights.get("credibility", 8.0),
        "ret_1d": model_weights.get("ret_1d", 8.0),
        "vol_z": model_weights.get("vol_z", 10.0),
        "vwap_dev": model_weights.get("vwap_dev", 6.0),
        "gap": model_weights.get("gap_pct", 4.0),
        "sector_momo": model_weights.get("sector_momo_pct", 6.0),
        "earnings_prox": model_weights.get("earnings_in_days", 4.0),
    }

    reasons = []
    v = 0.0  # Raw score accumulator

    # === NEWS FEATURES ===

    # Sentiment (entity-targeted)
    sentiment = features.get("sentiment", 0.0)
    sent_contrib = weights["news_sent"] * sentiment
    v += sent_contrib
    if abs(sent_contrib) > 2:
        reasons.append({
            "k": "sentiment",
            "v": round(sentiment, 2),
            "+": round(sent_contrib, 1)
        })

    # Magnitude (materiality)
    magnitude = features.get("magnitude", 0.5)
    mag_contrib = weights["news_mag"] * magnitude
    v += mag_contrib
    if mag_contrib > 5:
        reasons.append({
            "k": "magnitude",
            "v": round(magnitude, 2),
            "+": round(mag_contrib, 1)
        })
    
    # Novelty (freshness)
    novelty = features.get("novelty", 0.5)
    nov_contrib = weights["novelty"] * novelty
    v += nov_contrib
    if nov_contrib > 5:
        reasons.append({
            "k": "novelty",
            "v": round(novelty, 2),
            "+": round(nov_contrib, 1)
        })
    
    # Credibility (source quality)
    credibility = features.get("credibility", 0.5)
    cred_contrib = weights["cred"] * credibility
    v += cred_contrib
    if cred_contrib > 4:
        reasons.append({
            "k": "credibility",
            "v": round(credibility, 2),
            "+": round(cred_contrib, 1)
        })
    
    # === MARKET/TAPE FEATURES ===
    
    # 1-day return
    ret_1d = features.get("ret_1d", 0.0)
    ret_contrib = weights["ret_1d"] * clip(ret_1d, -0.1, 0.1) * 5
    v += ret_contrib
    if abs(ret_contrib) > 2:
        reasons.append({
            "k": "ret_1d",
            "v": f"{ret_1d*100:.1f}%",
            "+": round(ret_contrib, 1)
        })
    
    # Volume Z-score
    vol_z = features.get("vol_z", 0.0)
    vol_contrib = weights["vol_z"] * clip(vol_z / 5, -1, 3)
    v += vol_contrib
    if vol_contrib > 3:
        reasons.append({
            "k": "vol_z",
            "v": round(vol_z, 1),
            "+": round(vol_contrib, 1)
        })
    
    # VWAP deviation
    vwap_dev = features.get("vwap_dev", 0.0)
    vwap_contrib = weights["vwap_dev"] * clip(vwap_dev, -0.02, 0.02) * 50
    v += vwap_contrib
    if abs(vwap_contrib) > 2:
        reasons.append({
            "k": "vwap_dev",
            "v": f"{vwap_dev*100:.2f}%",
            "+": round(vwap_contrib, 1)
        })
    
    # Gap %
    gap_pct = features.get("gap_pct", 0.0)
    gap_contrib = weights["gap"] * clip(gap_pct, -0.05, 0.05) * 10
    v += gap_contrib
    if abs(gap_contrib) > 1.5:
        reasons.append({
            "k": "gap_pct",
            "v": f"{gap_pct*100:.1f}%",
            "+": round(gap_contrib, 1)
        })
    
    # === CALENDAR/CONTEXT FEATURES ===
    
    # Earnings proximity
    earnings_in_days = features.get("earnings_in_days", 999)
    if earnings_in_days <= 2:
        earn_boost = 1.0
    elif earnings_in_days <= 7:
        earn_boost = 0.5
    else:
        earn_boost = 0.0
    
    earn_contrib = weights["earnings_prox"] * earn_boost
    v += earn_contrib
    if earn_contrib > 3:
        reasons.append({
            "k": "earnings_in_days",
            "v": earnings_in_days,
            "+": round(earn_contrib, 1)
        })
    
    # Sector momentum
    sector_pct = features.get("sector_momo_pct", 0.5)
    sector_contrib = weights["sector_momo"] * (sector_pct - 0.5) * 2
    v += sector_contrib
    if abs(sector_contrib) > 2:
        reasons.append({
            "k": "sector_momo_pct",
            "v": f"{sector_pct*100:.0f}%",
            "+": round(sector_contrib, 1)
        })
    
    # === TOPIC NUDGES ===
    
    topic = features.get("topic", "")
    topic_contrib = 0.0
    
    if topic == "guidance_up":
        topic_contrib = 8
        v += topic_contrib
        reasons.append({"k": "topic", "v": "guidance_up", "+": topic_contrib})
    elif topic == "guidance_down":
        topic_contrib = -10
        v += topic_contrib
        reasons.append({"k": "topic", "v": "guidance_down", "+": topic_contrib})
    elif topic == "M&A":
        topic_contrib = 6
        v += topic_contrib
        reasons.append({"k": "topic", "v": "M&A", "+": topic_contrib})
    elif topic == "litigation":
        topic_contrib = -6
        v += topic_contrib
        reasons.append({"k": "topic", "v": "litigation", "+": topic_contrib})
    elif topic == "downgrade":
        topic_contrib = -5
        v += topic_contrib
        reasons.append({"k": "topic", "v": "downgrade", "+": topic_contrib})
    elif topic == "upgrade":
        topic_contrib = 5
        v += topic_contrib
        reasons.append({"k": "topic", "v": "upgrade", "+": topic_contrib})
    elif topic == "earnings":
        topic_contrib = 4
        v += topic_contrib
        reasons.append({"k": "topic", "v": "earnings", "+": topic_contrib})
    
    # === RISK TRIMS ===
    
    # Trading halted
    if features.get("halted", False):
        v -= 50
        reasons.append({"k": "risk_halted", "v": True, "+": -50})
    
    # High beta (risky)
    beta = features.get("beta", 1.0)
    if beta > 2.2:
        beta_trim = -6
        v += beta_trim
        reasons.append({"k": "risk_beta", "v": round(beta, 2), "+": beta_trim})
    
    # High ATR (volatile)
    atr_pct = features.get("atr_pct", 0.0)
    if atr_pct > 0.08:
        atr_trim = -5
        v += atr_trim
        reasons.append({"k": "risk_atr_pct", "v": f"{atr_pct*100:.1f}%", "+": atr_trim})
    
    # === SQUASH TO 0..100 ===
    
    score = 100 / (1 + math.exp(-0.06 * v))
    score = round(score, 1)
    
    # === LABEL ===
    
    if score >= 75:
        label = "High-Conviction"
    elif score >= 60:
        label = "Opportunity"
    elif score >= 45:
        label = "Watch"
    else:
        label = "Ignore"
    
    # === RESULT ===
    
    result = {
        "score": score,
        "label": label,
        "reasons": reasons,
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        "raw_score": round(v, 2),  # For debugging/calibration
    }
    
    logger.info(f"Calculated score: {score} ({label}) from raw={v:.1f}")
    
    return result


def extract_news_features(article: Dict, llm_plan: Optional[Dict] = None) -> Dict:
    """
    Extract news features from article and LLM analysis.
    
    Args:
        article: Article dict with title, summary, etc.
        llm_plan: LLM analysis result (optional)
    
    Returns:
        Dict with sentiment, magnitude, novelty, credibility, topic
    """
    features = {}
    
    if llm_plan:
        # Sentiment: map stance to [-1, 1]
        stance = llm_plan.get("stance", "NEUTRAL")
        if stance == "BULLISH":
            features["sentiment"] = llm_plan.get("confidence_0to1", 0.5)
        elif stance == "BEARISH":
            features["sentiment"] = -llm_plan.get("confidence_0to1", 0.5)
        else:
            features["sentiment"] = 0.0
        
        # Magnitude: use confidence as proxy
        features["magnitude"] = llm_plan.get("confidence_0to1", 0.5)
        
        # Topic: map catalyst_type
        catalyst_type = llm_plan.get("catalyst_type", "OTHER")
        if catalyst_type == "EARNINGS":
            features["topic"] = "earnings"
        elif catalyst_type == "GUIDANCE":
            features["topic"] = "guidance_up" if stance == "BULLISH" else "guidance_down"
        elif catalyst_type == "M&A":
            features["topic"] = "M&A"
        else:
            features["topic"] = "other"
    else:
        # Defaults if no LLM analysis
        features["sentiment"] = 0.0
        features["magnitude"] = 0.5
        features["topic"] = "other"
    
    # Novelty: based on published_at (fresher = higher)
    # For now, default to 0.8 (assume most articles are fresh)
    features["novelty"] = 0.8
    
    # Credibility: based on source
    source = article.get("source_name", "")
    if "SEC" in source or "Federal Reserve" in source:
        features["credibility"] = 0.9
    elif "Bloomberg" in source or "Reuters" in source or "WSJ" in source:
        features["credibility"] = 0.85
    else:
        features["credibility"] = 0.7
    
    return features

