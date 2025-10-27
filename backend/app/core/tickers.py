"""Ticker extraction and validation."""
import re
import json
import os
from pathlib import Path

# Load ticker symbols
TICKER_FILE = Path(__file__).parent.parent / "data" / "tickers.json"
VALID_TICKERS = set()

if TICKER_FILE.exists():
    try:
        with open(TICKER_FILE) as f:
            data = json.load(f)
            VALID_TICKERS = set(data.get("symbols", []))
    except Exception:
        pass


def extract_ticker(text: str) -> str | None:
    """
    Extract ticker symbol from text.
    
    Looks for patterns like (AAPL) or $AAPL.
    Returns the first valid ticker found, or None.
    """
    if not text:
        return None
    
    # Pattern 1: (TICKER)
    match = re.search(r'\(([A-Z]{1,5})\)', text)
    if match:
        ticker = match.group(1)
        if is_valid_ticker(ticker):
            return ticker
    
    # Pattern 2: $TICKER
    match = re.search(r'\$([A-Z]{1,5})\b', text)
    if match:
        ticker = match.group(1)
        if is_valid_ticker(ticker):
            return ticker
    
    return None


def is_valid_ticker(ticker: str) -> bool:
    """Check if ticker is in our known list."""
    if not VALID_TICKERS:
        # If no tickers loaded, accept 1-5 uppercase letters
        return bool(re.match(r'^[A-Z]{1,5}$', ticker))
    return ticker in VALID_TICKERS

