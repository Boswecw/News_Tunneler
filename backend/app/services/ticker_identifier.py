"""
Ticker Identifier Service

Resolves messy article text into tradable ticker symbols using:
- Cashtags ($AAPL, $TSLA)
- Company names and aliases
- Product/brand to parent company mapping
- Fuzzy matching with disambiguation
"""
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from app.core.logging import logger


# Symbol map database (in-memory for MVP, move to DB later)
SYMBOL_MAP: Dict[str, Dict] = {
    "AAPL": {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "aliases": ["Apple", "Apple Computer", "AAPL Inc.", "Apple Inc"],
        "brands": ["iPhone", "iPad", "Mac", "Apple Watch", "Vision Pro", "AirPods", "MacBook"],
        "exchange": "NASDAQ",
        "country": "US",
    },
    "TSLA": {
        "symbol": "TSLA",
        "name": "Tesla, Inc.",
        "aliases": ["Tesla", "Tesla Motors", "Tesla Inc"],
        "brands": ["Model S", "Model 3", "Model X", "Model Y", "Cybertruck", "Powerwall"],
        "exchange": "NASDAQ",
        "country": "US",
    },
    "NVDA": {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "aliases": ["NVIDIA", "Nvidia", "nVidia"],
        "brands": ["GeForce", "RTX", "CUDA", "Tegra"],
        "exchange": "NASDAQ",
        "country": "US",
    },
    "MSFT": {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "aliases": ["Microsoft", "MSFT Corp"],
        "brands": ["Windows", "Xbox", "Azure", "Office 365", "Teams", "Surface"],
        "exchange": "NASDAQ",
        "country": "US",
    },
    "GOOGL": {
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "aliases": ["Alphabet", "Google", "Alphabet Inc"],
        "brands": ["Google Search", "YouTube", "Android", "Chrome", "Pixel"],
        "exchange": "NASDAQ",
        "country": "US",
    },
    "AMZN": {
        "symbol": "AMZN",
        "name": "Amazon.com, Inc.",
        "aliases": ["Amazon", "Amazon.com", "AWS"],
        "brands": ["Prime", "Alexa", "Kindle", "Fire TV"],
        "exchange": "NASDAQ",
        "country": "US",
    },
    "META": {
        "symbol": "META",
        "name": "Meta Platforms, Inc.",
        "aliases": ["Meta", "Meta Platforms", "Facebook"],
        "brands": ["Facebook", "Instagram", "WhatsApp", "Oculus", "Quest"],
        "exchange": "NASDAQ",
        "country": "US",
    },
    "JPM": {
        "symbol": "JPM",
        "name": "JPMorgan Chase & Co.",
        "aliases": ["JPMorgan", "JP Morgan", "JPMorgan Chase", "Chase"],
        "exchange": "NYSE",
        "country": "US",
    },
    "BAC": {
        "symbol": "BAC",
        "name": "Bank of America Corporation",
        "aliases": ["Bank of America", "BofA", "BoA"],
        "exchange": "NYSE",
        "country": "US",
    },
    "GS": {
        "symbol": "GS",
        "name": "The Goldman Sachs Group, Inc.",
        "aliases": ["Goldman Sachs", "Goldman"],
        "exchange": "NYSE",
        "country": "US",
    },
    "SHW": {
        "symbol": "SHW",
        "name": "The Sherwin-Williams Company",
        "aliases": ["Sherwin-Williams", "Sherwin Williams"],
        "exchange": "NYSE",
        "country": "US",
    },
}

# Common words to ignore (not tickers)
IGNORE_WORDS = {
    "meta", "the", "inc", "corp", "corporation", "company", "group", "holdings",
    "limited", "llc", "lp", "trust", "fund", "etf", "index"
}

# Finance context keywords (boost score when near ticker mention)
FINANCE_KEYWORDS = {
    "earnings", "guidance", "sec", "downgrade", "upgrade", "analyst", "rating",
    "revenue", "profit", "loss", "beat", "miss", "outlook", "forecast",
    "merger", "acquisition", "buyout", "ipo", "filing", "10-q", "10-k",
    "dividend", "split", "buyback", "shares", "stock", "price target"
}


def extract_cashtags(text: str) -> List[str]:
    """Extract cashtags like $AAPL, $TSLA from text."""
    pattern = r'\$([A-Z]{1,5})\b'
    matches = re.findall(pattern, text)
    return [m for m in matches if m in SYMBOL_MAP]


def fuzzy_match_score(s1: str, s2: str) -> float:
    """Calculate fuzzy match score between two strings (0-1)."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def find_ticker_by_name(text: str, context: str = "") -> List[Tuple[str, float, str]]:
    """
    Find tickers by company name or alias with scoring.
    
    Returns list of (symbol, score, match_type) tuples.
    """
    text_lower = text.lower()
    context_lower = context.lower()
    candidates = []
    
    for symbol, data in SYMBOL_MAP.items():
        # Check exact name match
        if data["name"].lower() in text_lower:
            score = 1.0
            # Boost if in title/lead
            if data["name"].lower() in context_lower[:200]:
                score += 0.2
            # Boost if finance keywords nearby
            if any(kw in context_lower for kw in FINANCE_KEYWORDS):
                score += 0.1
            candidates.append((symbol, score, "exact_name"))
            continue
        
        # Check alias matches
        for alias in data["aliases"]:
            if len(alias) < 3:  # Skip very short aliases
                continue
            if alias.lower() in text_lower:
                score = 0.9
                if alias.lower() in context_lower[:200]:
                    score += 0.2
                if any(kw in context_lower for kw in FINANCE_KEYWORDS):
                    score += 0.1
                candidates.append((symbol, score, f"alias:{alias}"))
                break
        
        # Check brand matches (map to parent)
        for brand in data.get("brands", []):
            if len(brand) < 4:  # Skip very short brands
                continue
            if brand.lower() in text_lower:
                score = 0.7
                if brand.lower() in context_lower[:200]:
                    score += 0.1
                candidates.append((symbol, score, f"brand:{brand}"))
                break
        
        # Fuzzy matching as fallback
        for alias in [data["name"]] + data["aliases"]:
            if len(alias) < 4:
                continue
            fuzzy_score = fuzzy_match_score(alias, text)
            if fuzzy_score > 0.85:  # High threshold for fuzzy
                score = fuzzy_score * 0.8
                if any(kw in context_lower for kw in FINANCE_KEYWORDS):
                    score += 0.1
                candidates.append((symbol, score, f"fuzzy:{alias}"))
                break
    
    # Deduplicate and sort by score
    seen = set()
    unique_candidates = []
    for symbol, score, match_type in sorted(candidates, key=lambda x: x[1], reverse=True):
        if symbol not in seen:
            seen.add(symbol)
            unique_candidates.append((symbol, score, match_type))
    
    return unique_candidates


def resolve_tickers(title: str, summary: str, full_text: str = "") -> List[Dict]:
    """
    Main ticker resolution function.
    
    Returns list of ticker matches with metadata:
    [
        {
            "symbol": "AAPL",
            "confidence": 0.95,
            "match_type": "cashtag",
            "source": "title"
        },
        ...
    ]
    """
    results = []
    seen_symbols = set()
    
    # 1. Extract cashtags (highest confidence)
    cashtags_title = extract_cashtags(title)
    cashtags_summary = extract_cashtags(summary)
    cashtags_full = extract_cashtags(full_text) if full_text else []
    
    for symbol in cashtags_title:
        if symbol not in seen_symbols:
            results.append({
                "symbol": symbol,
                "confidence": 1.0,
                "match_type": "cashtag",
                "source": "title"
            })
            seen_symbols.add(symbol)
    
    for symbol in cashtags_summary:
        if symbol not in seen_symbols:
            results.append({
                "symbol": symbol,
                "confidence": 0.95,
                "match_type": "cashtag",
                "source": "summary"
            })
            seen_symbols.add(symbol)
    
    for symbol in cashtags_full:
        if symbol not in seen_symbols:
            results.append({
                "symbol": symbol,
                "confidence": 0.9,
                "match_type": "cashtag",
                "source": "full_text"
            })
            seen_symbols.add(symbol)
    
    # 2. Name/alias/brand matching
    context = f"{title} {summary} {full_text[:500]}"
    
    # Check title first (highest priority)
    title_matches = find_ticker_by_name(title, context)
    for symbol, score, match_type in title_matches:
        if symbol not in seen_symbols and score > 0.7:
            results.append({
                "symbol": symbol,
                "confidence": min(score, 0.95),
                "match_type": match_type,
                "source": "title"
            })
            seen_symbols.add(symbol)
    
    # Check summary
    summary_matches = find_ticker_by_name(summary, context)
    for symbol, score, match_type in summary_matches:
        if symbol not in seen_symbols and score > 0.75:
            results.append({
                "symbol": symbol,
                "confidence": min(score * 0.9, 0.9),
                "match_type": match_type,
                "source": "summary"
            })
            seen_symbols.add(symbol)
    
    # Check full text (lower threshold)
    if full_text:
        full_matches = find_ticker_by_name(full_text, context)
        for symbol, score, match_type in full_matches:
            if symbol not in seen_symbols and score > 0.8:
                results.append({
                    "symbol": symbol,
                    "confidence": min(score * 0.85, 0.85),
                    "match_type": match_type,
                    "source": "full_text"
                })
                seen_symbols.add(symbol)
    
    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    logger.info(f"Resolved {len(results)} tickers from article: {[r['symbol'] for r in results]}")
    
    return results


def get_symbol_info(symbol: str) -> Optional[Dict]:
    """Get full symbol information from the map."""
    return SYMBOL_MAP.get(symbol.upper())

