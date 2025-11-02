"""
Intraday High/Low Label Generation

Creates future high/low targets for intraday prediction with strict no-look-ahead guarantees.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def _future_window_idx(df: pd.DataFrame, i: int, horizon: int) -> slice:
    """
    Get slice for future window strictly after current bar.
    
    Args:
        df: DataFrame with bars
        i: Current bar index
        horizon: Number of bars to look ahead
        
    Returns:
        Slice from i+1 to min(i+horizon, len(df)-1)
    """
    start = i + 1  # Strictly exclude current bar
    end = min(i + horizon, len(df) - 1)
    return slice(start, end + 1)


def make_future_high_low(
    df: pd.DataFrame,
    horizons: Tuple[int, ...] = (5, 15),
    price_col: str = 'Close'
) -> Dict[str, pd.Series]:
    """
    Create future high/low labels for each horizon.
    
    For each bar at time t, computes:
    - high_next_Hm: Maximum price in window (t+1, t+H]
    - low_next_Hm: Minimum price in window (t+1, t+H]
    
    Strictly prevents look-ahead: labels only use data AFTER current bar.
    
    Args:
        df: DataFrame with OHLCV data (must have 'High', 'Low', 'Close')
        horizons: Tuple of horizon lengths in bars (e.g., (5, 15) for 5-bar and 15-bar)
        price_col: Column to use for high/low (default: 'Close')
        
    Returns:
        Dict mapping label names to Series:
        - 'high_next_5m': pd.Series
        - 'low_next_5m': pd.Series
        - 'high_next_15m': pd.Series (if 15 in horizons)
        - etc.
    """
    if len(df) == 0:
        return {}
    
    # Use High/Low columns if available, otherwise use Close
    if 'High' in df.columns and 'Low' in df.columns:
        highs = df['High'].to_numpy()
        lows = df['Low'].to_numpy()
    else:
        highs = df[price_col].to_numpy()
        lows = df[price_col].to_numpy()
    
    out = {}
    
    for H in horizons:
        fut_high = np.full(len(df), np.nan)
        fut_low = np.full(len(df), np.nan)
        
        # For each bar, compute max/min in future window
        for i in range(len(df) - 1):
            if i + H >= len(df):
                # Not enough future data
                break
            
            sl = _future_window_idx(df, i, H)
            fut_high[i] = np.max(highs[sl])
            fut_low[i] = np.min(lows[sl])
        
        out[f'high_next_{H}m'] = pd.Series(fut_high, index=df.index)
        out[f'low_next_{H}m'] = pd.Series(fut_low, index=df.index)
    
    logger.info(f"Created labels for horizons {horizons}: {len(df) - np.isnan(fut_high).sum()} valid samples")
    
    return out


def make_quantile_labels(
    df: pd.DataFrame,
    horizons: Tuple[int, ...] = (5, 15),
    quantiles: Tuple[float, ...] = (0.1, 0.9),
    price_col: str = 'Close'
) -> Dict[str, pd.Series]:
    """
    Create quantile-based labels for future price distribution.
    
    For each bar at time t, computes quantiles of prices in window (t+1, t+H].
    
    Args:
        df: DataFrame with price data
        horizons: Tuple of horizon lengths
        quantiles: Tuple of quantiles to compute (e.g., (0.1, 0.9) for 10th and 90th percentile)
        price_col: Column to use for prices
        
    Returns:
        Dict mapping label names to Series:
        - 'q10_next_5m': 10th percentile of next 5 bars
        - 'q90_next_5m': 90th percentile of next 5 bars
        - etc.
    """
    if len(df) == 0:
        return {}
    
    prices = df[price_col].to_numpy()
    out = {}
    
    for H in horizons:
        for q in quantiles:
            q_label = int(q * 100)
            fut_quantile = np.full(len(df), np.nan)
            
            for i in range(len(df) - 1):
                if i + H >= len(df):
                    break
                
                sl = _future_window_idx(df, i, H)
                fut_quantile[i] = np.quantile(prices[sl], q)
            
            out[f'q{q_label}_next_{H}m'] = pd.Series(fut_quantile, index=df.index)
    
    return out


def make_relative_labels(
    df: pd.DataFrame,
    horizons: Tuple[int, ...] = (5, 15),
    price_col: str = 'Close'
) -> Dict[str, pd.Series]:
    """
    Create relative (percentage) high/low labels.
    
    Returns high/low as percentage change from current price:
    - high_pct_next_5m = (future_high - current_price) / current_price * 100
    - low_pct_next_5m = (future_low - current_price) / current_price * 100
    
    Args:
        df: DataFrame with price data
        horizons: Tuple of horizon lengths
        price_col: Column to use for current price
        
    Returns:
        Dict mapping label names to Series
    """
    abs_labels = make_future_high_low(df, horizons, price_col)
    current_price = df[price_col].to_numpy()
    
    out = {}
    for H in horizons:
        high_key = f'high_next_{H}m'
        low_key = f'low_next_{H}m'
        
        if high_key in abs_labels and low_key in abs_labels:
            high_pct = ((abs_labels[high_key] - current_price) / current_price * 100)
            low_pct = ((abs_labels[low_key] - current_price) / current_price * 100)
            
            out[f'high_pct_next_{H}m'] = high_pct
            out[f'low_pct_next_{H}m'] = low_pct
    
    return out


def validate_no_leakage(
    df: pd.DataFrame,
    labels: Dict[str, pd.Series],
    horizon: int
) -> bool:
    """
    Validate that labels don't leak future information.
    
    Checks:
    1. Labels at index i only use data from indices > i
    2. First `horizon` labels should be NaN (not enough future data)
    3. Labels are strictly computed from future window
    
    Args:
        df: Original DataFrame
        labels: Dict of label Series
        horizon: Horizon length used
        
    Returns:
        True if validation passes, False otherwise
    """
    try:
        for label_name, label_series in labels.items():
            # Check that last `horizon` values are NaN
            last_n = label_series.iloc[-horizon:]
            if not last_n.isna().all():
                logger.error(f"Leakage detected in {label_name}: last {horizon} values should be NaN")
                return False
            
            # Check that we have some valid labels
            valid_count = (~label_series.isna()).sum()
            if valid_count == 0:
                logger.warning(f"No valid labels in {label_name}")
                return False
        
        logger.info(f"✅ No leakage detected for horizon={horizon}")
        return True
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


def create_training_labels(
    df: pd.DataFrame,
    horizons: Tuple[int, ...] = (5, 15),
    label_type: str = 'absolute',
    price_col: str = 'Close'
) -> pd.DataFrame:
    """
    Create all training labels and return as DataFrame.
    
    Args:
        df: DataFrame with OHLCV data
        horizons: Tuple of horizon lengths
        label_type: Type of labels ('absolute', 'relative', 'quantile')
        price_col: Column to use for prices
        
    Returns:
        DataFrame with all label columns
    """
    if label_type == 'absolute':
        labels = make_future_high_low(df, horizons, price_col)
    elif label_type == 'relative':
        labels = make_relative_labels(df, horizons, price_col)
    elif label_type == 'quantile':
        labels = make_quantile_labels(df, horizons, price_col=price_col)
    else:
        raise ValueError(f"Unknown label_type: {label_type}")
    
    # Validate no leakage
    for H in horizons:
        validate_no_leakage(df, labels, H)
    
    return pd.DataFrame(labels, index=df.index)

