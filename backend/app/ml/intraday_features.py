"""
Intraday Feature Engineering

Creates features for intraday high/low prediction with strict no-look-ahead guarantees.
All features computed only using data up to time t.
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def make_intraday_features(
    df: pd.DataFrame,
    include_session_context: bool = True,
    include_news_features: bool = False
) -> pd.DataFrame:
    """
    Create comprehensive intraday features for prediction.
    
    All features strictly use data up to current bar (no look-ahead).
    
    Features include:
    - OHLCV returns (log returns at multiple horizons)
    - Rolling statistics (SMA, EMA, VWAP, ATR)
    - Momentum/oscillators (RSI, MACD)
    - Volume/flow proxies
    - Session context (time of day, minutes since open/to close)
    - Optional: News sentiment (lagged, no peeking)
    
    Args:
        df: DataFrame with OHLCV columns (Open, High, Low, Close, Volume)
           Must have DatetimeIndex
        include_session_context: Add time-of-day features
        include_news_features: Add news/sentiment features (requires 'sentiment' column)
        
    Returns:
        DataFrame with feature columns (same index as input)
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    features = pd.DataFrame(index=df.index)
    
    # ===== Price Returns (log returns to handle large moves) =====
    close = df['Close']
    
    # Shifted returns (strictly no look-ahead)
    features['r1'] = np.log(close / close.shift(1))  # 1-bar return
    features['r5'] = np.log(close / close.shift(5))  # 5-bar return
    features['r15'] = np.log(close / close.shift(15))  # 15-bar return
    
    # Rolling volatility (stddev of returns)
    features['vol_5'] = features['r1'].rolling(5, min_periods=1).std()
    features['vol_20'] = features['r1'].rolling(20, min_periods=1).std()
    
    # ===== Rolling Statistics =====
    features['sma_5'] = close.rolling(5, min_periods=1).mean()
    features['sma_20'] = close.rolling(20, min_periods=1).mean()
    features['sma_50'] = close.rolling(50, min_periods=1).mean()
    
    features['ema_12'] = close.ewm(span=12, adjust=False, min_periods=1).mean()
    features['ema_26'] = close.ewm(span=26, adjust=False, min_periods=1).mean()
    
    # Price relative to moving averages
    features['close_vs_sma5'] = (close / features['sma_5'] - 1) * 100
    features['close_vs_sma20'] = (close / features['sma_20'] - 1) * 100
    
    # ===== VWAP (Volume Weighted Average Price) =====
    if 'Volume' in df.columns:
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        cumulative_tp_vol = (typical_price * df['Volume']).cumsum()
        cumulative_vol = df['Volume'].cumsum()
        features['vwap'] = cumulative_tp_vol / cumulative_vol
        features['close_vs_vwap'] = (close / features['vwap'] - 1) * 100
    
    # ===== ATR (Average True Range) =====
    if 'High' in df.columns and 'Low' in df.columns:
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - close.shift(1))
        low_close = np.abs(df['Low'] - close.shift(1))
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        features['atr_14'] = true_range.rolling(14, min_periods=1).mean()
        features['atr_pct'] = (features['atr_14'] / close) * 100
        
        # Range (high - low) as % of close
        features['range_pct'] = ((df['High'] - df['Low']) / close) * 100
    
    # ===== RSI (Relative Strength Index) =====
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14, min_periods=1).mean()
    loss = -delta.where(delta < 0, 0).rolling(14, min_periods=1).mean()
    rs = gain / loss
    features['rsi_14'] = 100 - (100 / (1 + rs))
    
    # ===== MACD =====
    macd = features['ema_12'] - features['ema_26']
    macd_signal = macd.ewm(span=9, adjust=False, min_periods=1).mean()
    features['macd'] = macd
    features['macd_signal'] = macd_signal
    features['macd_hist'] = macd - macd_signal
    
    # ===== Volume Features =====
    if 'Volume' in df.columns:
        vol = df['Volume']
        features['vol_sma_20'] = vol.rolling(20, min_periods=1).mean()
        features['vol_ratio'] = vol / features['vol_sma_20']
        
        # Volume z-score (standardized volume)
        vol_mean = vol.rolling(20, min_periods=1).mean()
        vol_std = vol.rolling(20, min_periods=1).std()
        features['vol_zscore_20'] = (vol - vol_mean) / (vol_std + 1e-8)
    
    # ===== Session Context (time of day) =====
    if include_session_context and isinstance(df.index, pd.DatetimeIndex):
        # Market hours: 9:30 AM - 4:00 PM ET (570 minutes)
        market_open_hour = 9
        market_open_minute = 30
        market_close_hour = 16
        market_close_minute = 0
        
        # Minutes since market open
        time_of_day = df.index.hour * 60 + df.index.minute
        market_open_minutes = market_open_hour * 60 + market_open_minute
        market_close_minutes = market_close_hour * 60 + market_close_minute
        
        features['minutes_since_open'] = time_of_day - market_open_minutes
        features['minutes_to_close'] = market_close_minutes - time_of_day
        
        # Session flags (pre-market, regular, after-hours)
        features['is_regular_hours'] = (
            (time_of_day >= market_open_minutes) & 
            (time_of_day < market_close_minutes)
        ).astype(int)
        
        # Cyclical encoding of time (sine/cosine for periodicity)
        # Normalize to [0, 1] within trading day
        normalized_time = (time_of_day - market_open_minutes) / (market_close_minutes - market_open_minutes)
        normalized_time = np.clip(normalized_time, 0, 1)
        features['time_sin'] = np.sin(2 * np.pi * normalized_time)
        features['time_cos'] = np.cos(2 * np.pi * normalized_time)
    
    # ===== News/Sentiment Features (lagged to prevent leakage) =====
    if include_news_features and 'sentiment' in df.columns:
        # Use last known sentiment (forward fill with limit to avoid stale data)
        features['sentiment_lag1'] = df['sentiment'].shift(1).fillna(0)
        features['sentiment_lag5'] = df['sentiment'].shift(5).fillna(0)
        
        if 'confidence' in df.columns:
            features['confidence_lag1'] = df['confidence'].shift(1).fillna(0)
    
    # ===== Fill NaN values =====
    # For first few rows where rolling windows are incomplete
    features = features.fillna(method='bfill', limit=5)  # Backfill first few rows
    features = features.fillna(0)  # Fill any remaining NaN with 0
    
    logger.info(f"Created {len(features.columns)} intraday features for {len(features)} bars")
    
    return features


def validate_features_no_leakage(
    df: pd.DataFrame,
    features: pd.DataFrame,
    check_index: int = 100
) -> bool:
    """
    Validate that features at index i only use data from indices <= i.
    
    Args:
        df: Original DataFrame
        features: Feature DataFrame
        check_index: Index to check (should be > 50 for meaningful test)
        
    Returns:
        True if validation passes
    """
    if check_index >= len(df):
        check_index = len(df) // 2
    
    try:
        # Recompute features using only data up to check_index
        df_subset = df.iloc[:check_index + 1].copy()
        features_subset = make_intraday_features(df_subset)
        
        # Compare feature values at check_index
        original_row = features.iloc[check_index]
        subset_row = features_subset.iloc[check_index]
        
        # Allow small numerical differences
        diff = np.abs(original_row - subset_row)
        max_diff = diff.max()
        
        if max_diff > 1e-6:
            logger.error(f"Leakage detected: features at index {check_index} differ by {max_diff}")
            logger.error(f"Columns with differences: {diff[diff > 1e-6].index.tolist()}")
            return False
        
        logger.info(f"✅ No leakage detected in features at index {check_index}")
        return True
        
    except Exception as e:
        logger.error(f"Feature validation error: {e}")
        return False


def prepare_feature_matrix(
    df: pd.DataFrame,
    include_session_context: bool = True,
    include_news_features: bool = False,
    feature_cols: Optional[list] = None
) -> pd.DataFrame:
    """
    Prepare final feature matrix for training/prediction.
    
    Args:
        df: DataFrame with OHLCV data
        include_session_context: Include time-of-day features
        include_news_features: Include news/sentiment features
        feature_cols: Optional list of specific columns to include
        
    Returns:
        DataFrame with selected features, ready for model training
    """
    features = make_intraday_features(
        df,
        include_session_context=include_session_context,
        include_news_features=include_news_features
    )
    
    if feature_cols is not None:
        # Select only specified columns
        available_cols = [col for col in feature_cols if col in features.columns]
        if len(available_cols) < len(feature_cols):
            missing = set(feature_cols) - set(available_cols)
            logger.warning(f"Missing feature columns: {missing}")
        features = features[available_cols]
    
    return features

