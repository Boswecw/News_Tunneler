"""
Price fetching service with support for Yahoo Finance and Polygon.io.

Provides functions to fetch closing prices and calculate index returns.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# In-memory cache with 1-hour TTL
_price_cache = {}
CACHE_TTL_SECONDS = 3600


def _cache_key(symbol: str, when: datetime) -> str:
    """Generate cache key for price lookup."""
    return f"{symbol}:{when.date()}"


def _get_from_cache(symbol: str, when: datetime) -> Optional[float]:
    """Get price from cache if available and not expired."""
    key = _cache_key(symbol, when)
    if key in _price_cache:
        price, timestamp = _price_cache[key]
        age = (datetime.now() - timestamp).total_seconds()
        if age < CACHE_TTL_SECONDS:
            return price
        else:
            del _price_cache[key]
    return None


def _put_in_cache(symbol: str, when: datetime, price: float):
    """Store price in cache."""
    key = _cache_key(symbol, when)
    _price_cache[key] = (price, datetime.now())


def _get_close_yahoo(symbol: str, when: datetime) -> Optional[float]:
    """Fetch closing price from Yahoo Finance."""
    try:
        import yfinance as yf
        
        # Fetch data with ±3 day buffer for weekends/holidays
        start = when - timedelta(days=3)
        end = when + timedelta(days=3)
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start, end=end)
        
        if hist.empty:
            logger.warning(f"No Yahoo data for {symbol} around {when.date()}")
            return None
        
        # Find closest date
        target_date = when.date()
        hist.index = hist.index.date
        
        if target_date in hist.index:
            return float(hist.loc[target_date]['Close'])
        
        # Find nearest date
        dates = sorted(hist.index)
        closest = min(dates, key=lambda d: abs((d - target_date).days))
        
        if abs((closest - target_date).days) <= 3:
            return float(hist.loc[closest]['Close'])
        
        logger.warning(f"No Yahoo data within 3 days of {when.date()} for {symbol}")
        return None
        
    except Exception as e:
        logger.error(f"Yahoo fetch error for {symbol}: {e}")
        return None


def _get_close_polygon(symbol: str, when: datetime) -> Optional[float]:
    """Fetch closing price from Polygon.io."""
    try:
        from polygon import RESTClient
        
        api_key = os.getenv("POLYGON_API_KEY")
        if not api_key:
            logger.error("POLYGON_API_KEY not set")
            return None
        
        client = RESTClient(api_key)
        
        # Try exact date first
        date_str = when.strftime("%Y-%m-%d")
        
        try:
            aggs = client.get_aggs(
                ticker=symbol,
                multiplier=1,
                timespan="day",
                from_=date_str,
                to=date_str,
            )
            
            if aggs and len(aggs) > 0:
                return float(aggs[0].close)
        except Exception:
            pass
        
        # Try ±3 day window
        start = (when - timedelta(days=3)).strftime("%Y-%m-%d")
        end = (when + timedelta(days=3)).strftime("%Y-%m-%d")
        
        aggs = client.get_aggs(
            ticker=symbol,
            multiplier=1,
            timespan="day",
            from_=start,
            to=end,
        )
        
        if not aggs or len(aggs) == 0:
            logger.warning(f"No Polygon data for {symbol} around {when.date()}")
            return None
        
        # Find closest date
        target_ts = int(when.timestamp() * 1000)
        closest = min(aggs, key=lambda a: abs(a.timestamp - target_ts))
        
        # Check if within 3 days
        closest_date = datetime.fromtimestamp(closest.timestamp / 1000)
        if abs((closest_date - when).days) <= 3:
            return float(closest.close)
        
        logger.warning(f"No Polygon data within 3 days of {when.date()} for {symbol}")
        return None
        
    except Exception as e:
        logger.error(f"Polygon fetch error for {symbol}: {e}")
        return None


def _is_index_symbol(symbol: str) -> bool:
    """Check if symbol is an index (starts with ^ or is a known index)."""
    if symbol.startswith("^"):
        return True

    # Common index symbols without ^ prefix
    known_indices = {
        "SPX", "DJI", "IXIC", "RUT", "VIX",  # US indices
        "FTSE", "DAX", "CAC", "NIKKEI",      # International
    }
    return symbol.upper() in known_indices


def get_close(symbol: str, when: datetime) -> Optional[float]:
    """
    Fetch closing price for a symbol at a given date.

    Intelligently routes requests:
    - Index symbols (^GSPC, ^DJI, etc.) → Yahoo Finance
    - Individual stocks (AAPL, NVDA, etc.) → Polygon.io (with Yahoo fallback)

    Uses cache first, then falls back to appropriate price source.
    Handles weekends/holidays by searching ±3 days.

    Args:
        symbol: Ticker symbol (e.g., "AAPL", "^GSPC")
        when: Target date/time

    Returns:
        Closing price or None if not found
    """
    # Check cache first
    cached = _get_from_cache(symbol, when)
    if cached is not None:
        return cached

    # Determine which source to use
    is_index = _is_index_symbol(symbol)
    use_source = os.getenv("USE_PRICE_SOURCE", "polygon").lower()

    # Always use Yahoo for indices (Polygon has rate limits for indices)
    if is_index:
        logger.debug(f"Using Yahoo Finance for index symbol: {symbol}")
        price = _get_close_yahoo(symbol, when)
    elif use_source == "polygon":
        # Try Polygon first for individual stocks
        logger.debug(f"Using Polygon for stock symbol: {symbol}")
        price = _get_close_polygon(symbol, when)

        # Fallback to Yahoo if Polygon fails
        if price is None:
            logger.info(f"Polygon failed for {symbol}, falling back to Yahoo Finance")
            price = _get_close_yahoo(symbol, when)
    elif use_source == "yahoo":
        logger.debug(f"Using Yahoo Finance for stock symbol: {symbol}")
        price = _get_close_yahoo(symbol, when)
    else:
        logger.error(f"Unknown price source: {use_source}")
        return None

    # Cache if found
    if price is not None:
        _put_in_cache(symbol, when, price)

    return price


def index_ret(index_symbol: str, d0: datetime, d1: datetime) -> float:
    """
    Calculate index return between two dates.
    
    Args:
        index_symbol: Index ticker (e.g., "^GSPC" for S&P 500)
        d0: Start date
        d1: End date
        
    Returns:
        Return as decimal (e.g., 0.02 for 2%)
    """
    p0 = get_close(index_symbol, d0)
    p1 = get_close(index_symbol, d1)
    
    if p0 is None or p1 is None:
        logger.warning(f"Could not calculate index return for {index_symbol}")
        return 0.0
    
    return (p1 / p0) - 1.0

