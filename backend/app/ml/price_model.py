"""
Price Prediction Model Training

Implements scikit-learn based price forecasting with:
- Technical indicator feature engineering
- Exponential time-decay weighting (10y mode)
- Walk-forward cross-validation
- Model persistence and compression
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import TimeSeriesSplit
import joblib
import pathlib


def calculate_indicators(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Calculate technical indicators for price prediction.
    
    Args:
        df: DataFrame with OHLCV columns (Open, High, Low, Close, Volume)
        config: Optional indicator configuration
        
    Returns:
        DataFrame with added indicator columns
    """
    if config is None:
        config = {
            "sma_periods": [5, 10, 20, 50],
            "ema_periods": [12, 26],
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "bb_period": 20,
            "bb_std": 2,
            "atr_period": 14
        }
    
    df = df.copy()
    
    # Simple Moving Averages
    for period in config.get("sma_periods", []):
        df[f"sma_{period}"] = df["Close"].rolling(window=period).mean()
    
    # Exponential Moving Averages
    for period in config.get("ema_periods", []):
        df[f"ema_{period}"] = df["Close"].ewm(span=period, adjust=False).mean()
    
    # RSI (Relative Strength Index)
    rsi_period = config.get("rsi_period", 14)
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    
    # MACD
    macd_fast = config.get("macd_fast", 12)
    macd_slow = config.get("macd_slow", 26)
    macd_signal = config.get("macd_signal", 9)
    ema_fast = df["Close"].ewm(span=macd_fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=macd_slow, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=macd_signal, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    
    # Bollinger Bands
    bb_period = config.get("bb_period", 20)
    bb_std = config.get("bb_std", 2)
    sma = df["Close"].rolling(window=bb_period).mean()
    std = df["Close"].rolling(window=bb_period).std()
    df["bb_upper"] = sma + (std * bb_std)
    df["bb_lower"] = sma - (std * bb_std)
    df["bb_width"] = df["bb_upper"] - df["bb_lower"]
    
    # ATR (Average True Range)
    atr_period = config.get("atr_period", 14)
    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())
    ranges = pd.DataFrame({
        'hl': high_low,
        'hc': high_close,
        'lc': low_close
    }, index=df.index)
    true_range = ranges.max(axis=1)
    df["atr"] = true_range.rolling(window=atr_period).mean()
    
    # Volume indicators
    volume_sma = df["Volume"].rolling(window=20).mean()
    df["volume_sma_20"] = volume_sma
    df["volume_ratio"] = df["Volume"].div(volume_sma)
    
    # Price momentum
    df["returns_1d"] = df["Close"].pct_change(1)
    df["returns_5d"] = df["Close"].pct_change(5)
    df["returns_20d"] = df["Close"].pct_change(20)
    
    return df


def compute_time_decay_weights(df: pd.DataFrame, half_life_days: int = 365) -> np.ndarray:
    """
    Compute exponential time-decay weights for training samples.
    
    More recent data gets higher weight. Uses exponential decay with configurable half-life.
    
    Args:
        df: DataFrame with DatetimeIndex
        half_life_days: Number of days for weight to decay to 50%
        
    Returns:
        Array of weights (same length as df)
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have DatetimeIndex")

    # Calculate days from most recent date
    most_recent = df.index.max()
    days_ago = (most_recent - df.index).days.values  # Convert to numpy array

    # Exponential decay: weight = 0.5^(days_ago / half_life)
    weights = np.power(0.5, days_ago / half_life_days)

    # Normalize to sum to 1
    weights = weights / weights.sum()

    return weights


def create_walk_forward_splits(
    n_samples: int,
    n_splits: int = 5,
    test_size: float = 0.2
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Create walk-forward cross-validation splits for time series.
    
    Ensures no look-ahead bias by always training on past data and testing on future data.
    
    Args:
        n_samples: Total number of samples
        n_splits: Number of CV splits
        test_size: Fraction of data to use for testing in each split
        
    Returns:
        List of (train_indices, test_indices) tuples
    """
    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=int(n_samples * test_size))
    return list(tscv.split(np.arange(n_samples)))


def prepare_features_and_target(
    df: pd.DataFrame,
    target_col: str = "Close",
    forecast_horizon: int = 1
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare feature matrix and target vector for training.
    
    Args:
        df: DataFrame with indicators already calculated
        target_col: Column to predict (default: "Close")
        forecast_horizon: Number of days ahead to predict (default: 1)
        
    Returns:
        Tuple of (features DataFrame, target Series)
    """
    # Select feature columns (exclude OHLCV and target)
    exclude_cols = ["Open", "High", "Low", "Close", "Volume", "Adj Close"]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].copy()
    
    # Target is future close price
    y = df[target_col].shift(-forecast_horizon)
    
    # Drop rows with NaN (from indicators or target shift)
    valid_idx = ~(X.isna().any(axis=1) | y.isna())
    X = X[valid_idx]
    y = y[valid_idx]
    
    return X, y


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    mode: str = "5y",
    sample_weights: Optional[np.ndarray] = None
) -> Pipeline:
    """
    Train price prediction model.
    
    Args:
        X: Feature matrix
        y: Target vector
        mode: Training mode ("5y" uses Ridge, "10y" uses RandomForest)
        sample_weights: Optional sample weights for training
        
    Returns:
        Trained sklearn Pipeline
    """
    if mode == "5y":
        # Fast baseline: Ridge regression
        model = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", Ridge(alpha=1.0))
        ])
    elif mode == "10y":
        # Robust: Random Forest with more trees
        model = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            ))
        ])
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be '5y' or '10y'")
    
    # Train model
    if sample_weights is not None:
        # For Ridge, weights are passed to fit
        # For RandomForest, weights are also supported
        model.fit(X, y, regressor__sample_weight=sample_weights)
    else:
        model.fit(X, y)
    
    return model


def evaluate_model(
    model: Pipeline,
    X: pd.DataFrame,
    y: pd.Series
) -> Dict[str, float]:
    """
    Evaluate model performance.
    
    Args:
        model: Trained model
        X: Feature matrix
        y: Target vector
        
    Returns:
        Dictionary with evaluation metrics
    """
    y_pred = model.predict(X)
    
    # R² score
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    # RMSE
    rmse = np.sqrt(np.mean((y - y_pred) ** 2))
    
    # MAE
    mae = np.mean(np.abs(y - y_pred))
    
    return {
        "r2": float(r2),
        "rmse": float(rmse),
        "mae": float(mae)
    }


def save_model(model: Pipeline, path: pathlib.Path, compress: int = 3) -> None:
    """
    Save model to disk with compression.
    
    Args:
        model: Trained model
        path: Path to save model
        compress: Compression level (0-9, higher = more compression)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path, compress=compress)


def load_model(path: pathlib.Path) -> Pipeline:
    """
    Load model from disk.
    
    Args:
        path: Path to model file
        
    Returns:
        Loaded model
    """
    return joblib.load(path)

