"""Price data fetching and technical analysis module."""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional
import httpx
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.db import get_db_context
from app.core.logging import logger
from app.models.price_cache import PriceCache

# Import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not installed - Yahoo Finance data source unavailable")

settings = get_settings()

VENDOR = os.getenv("PRIMARY_PRICE_VENDOR", "yfinance")  # Changed default to yfinance
AV_KEY = settings.alphavantage_key
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "900"))  # 15 minutes default


def _get_cached_data(db: Session, ticker: str, vendor: str, data_type: str) -> Optional[pd.DataFrame]:
    """Retrieve cached price data if still valid."""
    cache_entry = (
        db.query(PriceCache)
        .filter(
            PriceCache.ticker == ticker.upper(),
            PriceCache.vendor == vendor,
            PriceCache.data_type == data_type,
        )
        .order_by(PriceCache.fetched_at.desc())
        .first()
    )
    
    if cache_entry:
        # Check if cache is still valid
        age_seconds = (datetime.utcnow() - cache_entry.fetched_at).total_seconds()
        if age_seconds < CACHE_TTL:
            logger.info(f"Cache hit for {ticker} ({vendor}/{data_type}), age: {age_seconds:.0f}s")
            data = json.loads(cache_entry.payload_json)
            df = pd.DataFrame(data)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            return df
        else:
            logger.info(f"Cache expired for {ticker} ({vendor}/{data_type}), age: {age_seconds:.0f}s")
    
    return None


def _save_to_cache(db: Session, ticker: str, vendor: str, data_type: str, df: pd.DataFrame) -> None:
    """Save price data to cache."""
    # Convert DataFrame to JSON-serializable format
    data = df.copy()
    if "date" in data.columns:
        data["date"] = data["date"].astype(str)
    
    payload = data.to_dict(orient="records")
    
    cache_entry = PriceCache(
        ticker=ticker.upper(),
        vendor=vendor,
        data_type=data_type,
        payload_json=json.dumps(payload),
        fetched_at=datetime.utcnow(),
    )
    
    db.add(cache_entry)
    db.commit()
    logger.info(f"Cached {len(df)} rows for {ticker} ({vendor}/{data_type})")


def recompute_adjusted_from_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recompute adjusted close prices from raw close, dividend, and split data.

    This function rebuilds adjusted prices from raw close, dividend, and split data.
    Useful for verifying vendor data or switching data providers.

    Args:
        df: DataFrame with columns:
            - date (datetime): Trading date
            - close (float): Raw closing price
            - dividend (float): Dividend amount (0 if none)
            - split_coeff (float): Split coefficient (1 if none)

    Returns:
        DataFrame with additional column:
            - adj_close_rebuilt (float): Recomputed adjusted close price

    The adjustment applies cumulative factors FORWARD from each event date.
    Split factor: 1 / split_ratio (AV's 'split coefficient' is the ratio)
    Dividend factor: (prev_close - dividend) / prev_close on ex-div date
    """
    df = df.sort_values("date").reset_index(drop=True).copy()

    # Build per-day adjustment multipliers that affect *all prior* dates
    # Split factor: 1 / split_ratio (AV's 'split coefficient' is the ratio)
    split_factor = 1.0 / df["split_coeff"].replace(0, 1.0)

    # Dividend factor: (prev_close - dividend) / prev_close on ex-div date
    prev_close = df["close"].shift(1)
    div_factor = (prev_close - df["dividend"]) / prev_close
    div_factor = div_factor.fillna(1.0).clip(lower=1e-9, upper=1.0)  # safety

    # The per-day factor that should be applied to *prior* history is:
    per_day_factor = split_factor * div_factor

    # To adjust a date t, we need the product of factors from (t+1 ... end)
    # Compute cumulative product forward, then roll it back as a suffix product
    cumprod_forward = per_day_factor.cumprod()
    # Suffix product = total_cumprod / cumprod_up_to_t
    total = cumprod_forward.iloc[-1]
    suffix_factor = total / cumprod_forward
    suffix_factor = suffix_factor.fillna(1.0)

    df["adj_close_rebuilt"] = df["close"] * suffix_factor
    return df


def _alphavantage_daily(ticker: str) -> pd.DataFrame:
    """Fetch daily price data from Alpha Vantage."""
    if not AV_KEY:
        raise ValueError("ALPHAVANTAGE_KEY not configured")
    
    # Use TIME_SERIES_DAILY (free tier) instead of TIME_SERIES_DAILY_ADJUSTED (premium)
    url = (
        "https://www.alphavantage.co/query"
        "?function=TIME_SERIES_DAILY"
        f"&symbol={ticker}&outputsize=compact&apikey={AV_KEY}"
    )
    
    logger.info(f"Fetching daily prices for {ticker} from Alpha Vantage...")
    
    try:
        r = httpx.get(url, timeout=30)
        r.raise_for_status()
        js = r.json()
        
        # Check for API errors
        if "Error Message" in js:
            raise ValueError(f"Alpha Vantage error: {js['Error Message']}")
        if "Note" in js:
            raise ValueError(f"Alpha Vantage rate limit: {js['Note']}")
        if "Information" in js:
            raise ValueError(f"Alpha Vantage premium endpoint: {js['Information']}")
        
        ts = js.get("Time Series (Daily)", {})
        if not ts:
            raise ValueError(f"No price data returned for {ticker}")
        
        rows = []
        for d, o in ts.items():
            rows.append({
                "date": pd.Timestamp(d),
                "open": float(o["1. open"]),
                "high": float(o["2. high"]),
                "low": float(o["3. low"]),
                "close": float(o["4. close"]),
                "adj_close": float(o["4. close"]),  # No adjusted close in free tier
                "volume": int(float(o["5. volume"])),  # Volume is field 5 in TIME_SERIES_DAILY
                # Free tier doesn't include dividend/split data, set defaults
                # If you upgrade to premium or use another source, update these fields:
                "dividend": 0.0,  # Would be float(o.get("7. dividend amount", 0.0)) in premium
                "split_coeff": 1.0,  # Would be float(o.get("8. split coefficient", 1.0)) in premium
            })

        df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

        # Optional: Recompute adjusted close if we had dividend/split data
        # Since free tier has no events (dividend=0, split_coeff=1), this won't change anything
        # But it demonstrates the capability for when you upgrade or switch vendors
        if "dividend" in df.columns and "split_coeff" in df.columns:
            df = recompute_adjusted_from_events(df)
            # Compare vendor's adj_close with our rebuilt version (should match closely)
            if "adj_close_rebuilt" in df.columns:
                logger.debug(f"Adjusted close comparison: vendor vs rebuilt (should match for free tier)")

        logger.info(f"Fetched {len(df)} daily candles for {ticker}")
        return df
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching {ticker}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        raise


def _yfinance_daily(ticker: str) -> pd.DataFrame:
    """Fetch daily price data from Yahoo Finance (yfinance)."""
    if not YFINANCE_AVAILABLE:
        raise ValueError("yfinance library not installed")

    logger.info(f"Fetching daily prices for {ticker} from Yahoo Finance...")

    try:
        # Create ticker object
        stock = yf.Ticker(ticker)

        # Get 100 days of history (matching Alpha Vantage compact output)
        df = stock.history(period="100d")

        if df.empty:
            raise ValueError(f"No price data returned for {ticker}")

        # Get dividends and splits
        dividends = stock.dividends
        splits = stock.splits

        # Reset index to make Date a column
        df = df.reset_index()

        # Rename columns to match our schema
        df.columns = df.columns.str.lower()
        df = df.rename(columns={
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
        })

        # yfinance doesn't include 'Adj Close' in history() by default, but we can get it
        # Actually, it does include it - let me check the actual column names
        # The history() method returns: Open, High, Low, Close, Volume, Dividends, Stock Splits

        # Map dividend and split data to our dataframe
        df['dividend'] = 0.0
        df['split_coeff'] = 1.0

        # Add dividends (if any occurred in this period)
        if not dividends.empty:
            for div_date, div_amount in dividends.items():
                # Find matching date in our dataframe
                mask = df['date'].dt.date == div_date.date()
                if mask.any():
                    df.loc[mask, 'dividend'] = float(div_amount)

        # Add splits (if any occurred in this period)
        if not splits.empty:
            for split_date, split_ratio in splits.items():
                # Find matching date in our dataframe
                mask = df['date'].dt.date == split_date.date()
                if mask.any():
                    df.loc[mask, 'split_coeff'] = float(split_ratio)

        # Convert date to pandas Timestamp and remove timezone info
        # (to match the format expected by other parts of the system)
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)

        # For now, use close as adj_close (we'll recompute it)
        df['adj_close'] = df['close']

        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)

        # Recompute adjusted close from events
        if 'dividend' in df.columns and 'split_coeff' in df.columns:
            df = recompute_adjusted_from_events(df)
            logger.info(f"Recomputed adjusted close for {ticker} from dividend/split data")

        # Select only the columns we need
        df = df[['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'dividend', 'split_coeff']]

        # If we have adj_close_rebuilt, use it as the primary adj_close
        if 'adj_close_rebuilt' in df.columns:
            df['adj_close'] = df['adj_close_rebuilt']
            df = df.drop(columns=['adj_close_rebuilt'])

        logger.info(f"Fetched {len(df)} daily candles for {ticker} from Yahoo Finance")

        # Log if we found any corporate actions
        div_count = (df['dividend'] > 0).sum()
        split_count = (df['split_coeff'] != 1.0).sum()
        if div_count > 0 or split_count > 0:
            logger.info(f"Found {div_count} dividend(s) and {split_count} split(s) for {ticker}")

        return df

    except Exception as e:
        logger.error(f"Error fetching {ticker} from Yahoo Finance: {e}")
        raise


def _finnhub_daily(ticker: str) -> pd.DataFrame:
    """Fetch daily price data from Finnhub (fallback)."""
    if not FINNHUB_KEY:
        raise ValueError("FINNHUB_KEY not configured")
    
    # Get data for last 100 days
    end_ts = int(time.time())
    start_ts = end_ts - (100 * 24 * 60 * 60)
    
    url = (
        f"https://finnhub.io/api/v1/stock/candle"
        f"?symbol={ticker}&resolution=D&from={start_ts}&to={end_ts}&token={FINNHUB_KEY}"
    )
    
    logger.info(f"Fetching daily prices for {ticker} from Finnhub...")
    
    try:
        r = httpx.get(url, timeout=30)
        r.raise_for_status()
        js = r.json()
        
        if js.get("s") != "ok":
            raise ValueError(f"Finnhub error: {js.get('s', 'unknown')}")
        
        rows = []
        for i in range(len(js["t"])):
            rows.append({
                "date": pd.Timestamp(js["t"][i], unit="s"),
                "open": float(js["o"][i]),
                "high": float(js["h"][i]),
                "low": float(js["l"][i]),
                "close": float(js["c"][i]),
                "adj_close": float(js["c"][i]),  # Finnhub doesn't provide adjusted
                "volume": int(js["v"][i]),
            })
        
        df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
        logger.info(f"Fetched {len(df)} daily candles for {ticker}")
        return df
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching {ticker}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        raise


def get_daily_prices(ticker: str, use_cache: bool = True) -> pd.DataFrame:
    """
    Get daily price data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        use_cache: Whether to use cached data (default: True)
    
    Returns:
        DataFrame with columns: date, open, high, low, close, adj_close, volume
    """
    ticker = ticker.upper()
    
    with get_db_context() as db:
        # Try cache first
        if use_cache:
            cached = _get_cached_data(db, ticker, VENDOR, "daily")
            if cached is not None:
                return cached
        
        # Fetch fresh data
        try:
            if VENDOR == "yfinance":
                df = _yfinance_daily(ticker)
            elif VENDOR == "alphavantage":
                df = _alphavantage_daily(ticker)
            elif VENDOR == "finnhub":
                df = _finnhub_daily(ticker)
            else:
                raise ValueError(f"Unknown vendor: {VENDOR}")

            # Save to cache
            _save_to_cache(db, ticker, VENDOR, "daily", df)
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch prices for {ticker}: {e}")
            # Try to return stale cache as fallback
            cached = _get_cached_data(db, ticker, VENDOR, "daily")
            if cached is not None:
                logger.warning(f"Returning stale cache for {ticker}")
                return cached
            raise


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical indicators on price data.
    
    Args:
        df: DataFrame with OHLCV data
    
    Returns:
        DataFrame with added indicator columns
    """
    if df.empty:
        return df
    
    out = df.copy()
    
    # Simple Moving Averages
    out["sma20"] = out["adj_close"].rolling(20, min_periods=1).mean()
    out["sma50"] = out["adj_close"].rolling(50, min_periods=1).mean()
    
    # RSI (14-period)
    delta = out["adj_close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / (loss.replace(0, 1e-9))
    out["rsi14"] = 100 - (100 / (1 + rs))
    
    # ATR (14-period)
    high_low = out["high"] - out["low"]
    high_close = (out["high"] - out["adj_close"].shift()).abs()
    low_close = (out["low"] - out["adj_close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    out["atr14"] = tr.rolling(14, min_periods=1).mean()
    
    # 52-week high/low (252 trading days)
    out["52w_high"] = out["adj_close"].rolling(252, min_periods=1).max()
    out["52w_low"] = out["adj_close"].rolling(252, min_periods=1).min()
    out["from_52w_high_%"] = ((out["adj_close"] / out["52w_high"]) - 1) * 100
    out["from_52w_low_%"] = ((out["adj_close"] / out["52w_low"]) - 1) * 100
    
    # Volume moving average (30-day)
    out["volume_ma30"] = out["volume"].rolling(30, min_periods=1).mean()
    out["volume_vs_avg_%"] = ((out["volume"] / out["volume_ma30"]) - 1) * 100
    
    return out


def compute_gap_percent(df: pd.DataFrame, date: pd.Timestamp) -> Optional[float]:
    """
    Compute gap percentage on a specific date.
    
    Args:
        df: DataFrame with OHLCV data
        date: Date to compute gap for
    
    Returns:
        Gap percentage or None if not available
    """
    df = df.set_index("date").sort_index()
    
    if date not in df.index:
        # Find nearest trading day
        idx = df.index.searchsorted(date)
        if idx >= len(df.index):
            return None
        date = df.index[idx]
    
    loc = df.index.get_loc(date)
    if loc == 0:
        return None  # No prior day
    
    prior_close = df.iloc[loc - 1]["adj_close"]
    current_open = df.iloc[loc]["open"]
    
    gap_pct = ((current_open / prior_close) - 1) * 100
    return gap_pct

