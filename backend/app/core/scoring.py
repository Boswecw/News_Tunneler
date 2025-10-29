"""Scoring logic for articles."""
import re
from datetime import datetime, timedelta
from .sentiment import analyze_sentiment
from .cache import cache_result
from .resilience import with_fallback
from .logging import logger


def score_catalyst(title: str, summary: str) -> float:
    """
    Score catalyst potential (0-5).
    
    5 if: 8-K, guidance, beat, miss, acquire, merger, FDA, PDUFA, contract, award, buyback, investigation, export ban
    3 if: trial, phase, partnership, license, MoU
    0 otherwise
    """
    text = f"{title} {summary}".lower()
    
    high_catalyst_keywords = r"8-K|guidance|beat|miss|acquire|merger|FDA|PDUFA|contract|award|buyback|investigation|export ban"
    if re.search(high_catalyst_keywords, text, re.IGNORECASE):
        return 5.0
    
    medium_catalyst_keywords = r"trial|phase|partnership|license|MoU"
    if re.search(medium_catalyst_keywords, text, re.IGNORECASE):
        return 3.0
    
    return 0.0


def score_novelty(published_at: datetime) -> float:
    """
    Score novelty based on age (0-5).
    
    5 if age < 6h
    3 if age < 24h
    1 otherwise
    """
    age = datetime.utcnow() - published_at
    
    if age < timedelta(hours=6):
        return 5.0
    elif age < timedelta(hours=24):
        return 3.0
    else:
        return 1.0


def score_credibility(source_url: str) -> float:
    """
    Score credibility based on source domain (0-5).
    
    5 if domain in: sec.gov, investor., ir., prnewswire, globenewswire, businesswire
    3 otherwise
    """
    domain = source_url.lower()
    
    high_credibility_domains = [
        "sec.gov",
        "investor.",
        "ir.",
        "prnewswire",
        "globenewswire",
        "businesswire",
    ]
    
    for credible_domain in high_credibility_domains:
        if credible_domain in domain:
            return 5.0
    
    return 3.0


@cache_result(ttl=3600, key_prefix="liquidity")  # Cache for 1 hour
@with_fallback(fallback_value=0.0, log_error=True)
def score_liquidity(ticker: str | None) -> float:
    """
    Score liquidity based on average volume (0-5).

    5: >10M avg volume (highly liquid)
    4: 5M-10M
    3: 1M-5M
    2: 100K-1M
    1: 10K-100K
    0: <10K or no data

    Uses yfinance to get average volume data.
    Results are cached for 1 hour to reduce API calls.
    """
    if not ticker:
        return 0.0

    try:
        import yfinance as yf

        # Get stock info
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get average volume
        avg_volume = info.get('averageVolume', 0)

        # Score based on volume tiers
        if avg_volume >= 10_000_000:
            score = 5.0
        elif avg_volume >= 5_000_000:
            score = 4.0
        elif avg_volume >= 1_000_000:
            score = 3.0
        elif avg_volume >= 100_000:
            score = 2.0
        elif avg_volume >= 10_000:
            score = 1.0
        else:
            score = 0.0

        logger.debug(f"Liquidity score for {ticker}: {score} (avg_volume={avg_volume:,})")
        return score

    except Exception as e:
        logger.warning(f"Failed to get liquidity for {ticker}: {e}")
        return 0.0


def compute_total_score(
    catalyst: float,
    novelty: float,
    credibility: float,
    sentiment: float,
    liquidity: float,
    weights: dict[str, float] | None = None,
) -> float:
    """
    Compute total score with optional weights.
    
    Default weights are all 1.0.
    """
    if weights is None:
        weights = {
            "catalyst": 1.0,
            "novelty": 1.0,
            "credibility": 1.0,
            "sentiment": 1.0,
            "liquidity": 1.0,
        }
    
    total = (
        catalyst * weights.get("catalyst", 1.0)
        + novelty * weights.get("novelty", 1.0)
        + credibility * weights.get("credibility", 1.0)
        + sentiment * weights.get("sentiment", 1.0)
        + liquidity * weights.get("liquidity", 1.0)
    )
    
    return total

