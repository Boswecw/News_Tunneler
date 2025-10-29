"""
Ticker alias resolution service.

Maps company names, aliases, and brands to ticker symbols.
"""
from typing import Optional

# Basic ticker alias mapping
TICKER_ALIASES = {
    # Tech Giants
    "apple": "AAPL",
    "apple inc": "AAPL",
    "apple computer": "AAPL",
    "microsoft": "MSFT",
    "microsoft corporation": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "alphabet inc": "GOOGL",
    "amazon": "AMZN",
    "amazon.com": "AMZN",
    "meta": "META",
    "facebook": "META",
    "meta platforms": "META",
    "tesla": "TSLA",
    "tesla inc": "TSLA",
    "nvidia": "NVDA",
    "nvidia corporation": "NVDA",
    
    # Financial
    "jpmorgan": "JPM",
    "jpmorgan chase": "JPM",
    "jp morgan": "JPM",
    "bank of america": "BAC",
    "bofa": "BAC",
    "wells fargo": "WFC",
    "citigroup": "C",
    "citi": "C",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    
    # Consumer
    "walmart": "WMT",
    "target": "TGT",
    "costco": "COST",
    "home depot": "HD",
    "lowes": "LOW",
    "mcdonalds": "MCD",
    "starbucks": "SBUX",
    "nike": "NKE",
    "coca cola": "KO",
    "pepsi": "PEP",
    "pepsico": "PEP",
    
    # Healthcare
    "johnson & johnson": "JNJ",
    "pfizer": "PFE",
    "moderna": "MRNA",
    "abbvie": "ABBV",
    "merck": "MRK",
    "unitedhealth": "UNH",
    "cvs": "CVS",
    
    # Industrial
    "boeing": "BA",
    "caterpillar": "CAT",
    "3m": "MMM",
    "general electric": "GE",
    "ge": "GE",
    "honeywell": "HON",
    
    # Energy
    "exxon": "XOM",
    "exxonmobil": "XOM",
    "chevron": "CVX",
    "conocophillips": "COP",
    "schlumberger": "SLB",
    
    # Telecom
    "verizon": "VZ",
    "at&t": "T",
    "att": "T",
    "t-mobile": "TMUS",
    "comcast": "CMCSA",
    
    # Retail
    "sherwin williams": "SHW",
    "sherwin-williams": "SHW",
}


def resolve_ticker(name: str) -> Optional[str]:
    """
    Resolve a company name or alias to a ticker symbol.
    
    Args:
        name: Company name or alias
        
    Returns:
        Ticker symbol or None if not found
    """
    if not name:
        return None
    
    name_lower = name.lower().strip()
    
    # Direct lookup
    if name_lower in TICKER_ALIASES:
        return TICKER_ALIASES[name_lower]
    
    # Partial match (e.g., "Apple Inc." contains "apple")
    for alias, ticker in TICKER_ALIASES.items():
        if alias in name_lower or name_lower in alias:
            return ticker
    
    return None


def add_alias(name: str, ticker: str):
    """
    Add a new alias mapping.
    
    Args:
        name: Company name or alias
        ticker: Ticker symbol
    """
    TICKER_ALIASES[name.lower().strip()] = ticker.upper()

