"""
Backtest module for computing forward returns after news events.
"""
from datetime import timedelta
import pandas as pd
from typing import List, Dict, Any, Tuple, Union


def forward_returns(
    prices_df: pd.DataFrame,
    event_dates: List[Union[pd.Timestamp, str]],
    windows: Tuple[int, ...] = (1, 3, 5)
) -> Dict[str, Any]:
    """
    Compute forward returns from event dates.
    
    Args:
        prices_df: DataFrame with columns [date, adj_close] ascending by date
        event_dates: iterable of pd.Timestamp dates (market dates or ISO date strings)
        windows: tuple of forward-looking windows in trading days (default: 1, 3, 5)
    
    Returns:
        dict with per-window stats and per-event samples
        {
            "windows": {
                "1d": {"count": N, "avg_%": X, "median_%": Y, "win_rate_%": Z, ...},
                "3d": {...},
                "5d": {...}
            },
            "samples": [
                {"event_date": "2025-01-15", "1d_%": 2.5, "3d_%": 5.1, "5d_%": 3.2},
                ...
            ]
        }
    """
    # Prepare price data
    df = prices_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    # Ensure date is timezone-naive
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_localize(None)
    df = df.set_index("date").sort_index()
    
    out_samples = []

    for d in event_dates:
        # Convert to timestamp and remove timezone info to match price data
        d = pd.Timestamp(d).tz_localize(None).normalize()

        # Align to next trading day if event date is not a trading day
        if d not in df.index:
            pos = df.index.searchsorted(d)
            if pos >= len(df.index):
                continue
            d = df.index[pos]
        
        start_price = df.loc[d, "adj_close"]
        sample = {"event_date": d.date().isoformat()}
        
        # Calculate forward returns for each window
        for w in windows:
            idx = df.index.get_loc(d) + w
            if idx < len(df.index):
                end_price = df.iloc[idx]["adj_close"]
                fwd_return = (end_price / start_price - 1) * 100.0
                sample[f"{w}d_%"] = round(float(fwd_return), 2)
        
        out_samples.append(sample)
    
    # Aggregate statistics for each window
    def compute_stats(key: str) -> Dict[str, Any]:
        """Compute statistics for a specific window."""
        vals = [s[key] for s in out_samples if key in s]
        if not vals:
            return None
        
        wins = sum(1 for v in vals if v > 0)
        up_vals = [v for v in vals if v > 0]
        down_vals = [v for v in vals if v <= 0]
        
        return {
            "count": len(vals),
            "avg_%": round(float(pd.Series(vals).mean()), 2),
            "median_%": round(float(pd.Series(vals).median()), 2),
            "win_rate_%": round(100 * wins / len(vals), 1) if vals else 0.0,
            "avg_up_%": round(float(pd.Series(up_vals).mean()), 2) if up_vals else 0.0,
            "avg_down_%": round(float(pd.Series(down_vals).mean()), 2) if down_vals else 0.0
        }
    
    # Build aggregated results
    agg = {f"{w}d": compute_stats(f"{w}d_%") for w in windows}
    
    return {
        "windows": agg,
        "samples": out_samples
    }

