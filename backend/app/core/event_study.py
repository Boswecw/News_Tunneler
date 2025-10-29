"""Event study analysis for measuring stock reactions to news."""
from typing import Dict, List, Tuple
import pandas as pd
from app.core.logging import logger


def window_returns(
    df: pd.DataFrame,
    event_date: pd.Timestamp,
    windows: Tuple[int, ...] = (1, 3, 5)
) -> Dict[str, float]:
    """
    Calculate forward returns after an event date.
    
    Args:
        df: DataFrame with 'date' and 'adj_close' columns
        event_date: The event date (news publication date)
        windows: Tuple of forward-looking windows in trading days (default: 1, 3, 5)
    
    Returns:
        Dictionary with keys like "1d_%", "3d_%", "5d_%" containing percentage returns
    """
    if df.empty:
        return {}
    
    # Ensure date column is datetime
    df = df.copy()
    if "date" not in df.columns:
        logger.warning("DataFrame missing 'date' column")
        return {}
    
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    
    # Find the event date or next trading day
    if event_date not in df.index:
        idx = df.index.searchsorted(event_date)
        if idx >= len(df.index):
            logger.warning(f"Event date {event_date} is after all available data")
            return {}
        event_date = df.index[idx]
        logger.debug(f"Aligned event date to next trading day: {event_date}")
    
    event_loc = df.index.get_loc(event_date)
    base_price = df.iloc[event_loc]["adj_close"]
    
    results = {}
    for w in windows:
        target_loc = event_loc + w
        if target_loc < len(df.index):
            target_price = df.iloc[target_loc]["adj_close"]
            return_pct = ((target_price / base_price) - 1) * 100
            results[f"{w}d_%"] = return_pct
        else:
            logger.debug(f"Not enough data for {w}-day window from {event_date}")
    
    return results


def analyze_catalyst_history(
    df: pd.DataFrame,
    catalyst_dates: List[pd.Timestamp],
    windows: Tuple[int, ...] = (1, 3, 5)
) -> Dict[str, Dict[str, float]]:
    """
    Analyze average returns across multiple catalyst events.
    
    Args:
        df: DataFrame with 'date' and 'adj_close' columns
        catalyst_dates: List of event dates to analyze
        windows: Tuple of forward-looking windows in trading days
    
    Returns:
        Dictionary with statistics for each window:
        {
            "1d_%": {"mean": X, "median": Y, "std": Z, "count": N},
            "3d_%": {...},
            ...
        }
    """
    if df.empty or not catalyst_dates:
        return {}
    
    all_returns = {f"{w}d_%": [] for w in windows}
    
    for event_date in catalyst_dates:
        returns = window_returns(df, event_date, windows)
        for key, value in returns.items():
            if key in all_returns:
                all_returns[key].append(value)
    
    # Compute statistics
    stats = {}
    for window_key, values in all_returns.items():
        if values:
            series = pd.Series(values)
            stats[window_key] = {
                "mean": round(series.mean(), 2),
                "median": round(series.median(), 2),
                "std": round(series.std(), 2),
                "min": round(series.min(), 2),
                "max": round(series.max(), 2),
                "count": len(values),
            }
        else:
            stats[window_key] = {
                "mean": None,
                "median": None,
                "std": None,
                "min": None,
                "max": None,
                "count": 0,
            }
    
    return stats


def get_typical_reaction(
    df: pd.DataFrame,
    event_date: pd.Timestamp,
    windows: Tuple[int, ...] = (1, 3, 5)
) -> Dict[str, float]:
    """
    Get typical reaction for a single event (wrapper around window_returns).
    
    This is a convenience function that matches the API endpoint signature.
    
    Args:
        df: DataFrame with 'date' and 'adj_close' columns
        event_date: The event date
        windows: Tuple of forward-looking windows in trading days
    
    Returns:
        Dictionary with percentage returns for each window
    """
    return window_returns(df, event_date, windows)

