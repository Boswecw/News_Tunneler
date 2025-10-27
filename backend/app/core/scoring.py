"""Scoring logic for articles."""
import re
from datetime import datetime, timedelta
from .sentiment import analyze_sentiment


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


def score_liquidity(ticker: str | None) -> float:
    """
    Score liquidity (0-5).
    
    Currently returns 0 (placeholder for API integration).
    Can be enhanced with AlphaVantage or NewsAPI volume data.
    """
    # TODO: Integrate with AlphaVantage or NewsAPI for volume data
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

