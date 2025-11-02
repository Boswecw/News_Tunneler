"""
Training CLI for Intraday Bounds Prediction

Usage:
    python -m backend.app.ml.train_intraday_bounds --ticker AAPL --interval 1m --horizons 5 15 --days 30
"""
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple
import pandas as pd
import numpy as np
import yfinance as yf

from app.ml.intraday_features import make_intraday_features, validate_features_no_leakage
from app.ml.intraday_labels import create_training_labels, validate_no_leakage
from app.ml.intraday_models import (
    fit_quantile_model,
    evaluate_quantile_model,
    save_model
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_intraday_data(
    ticker: str,
    interval: str = '1m',
    days: int = 30
) -> pd.DataFrame:
    """
    Fetch intraday data from yfinance.
    
    Args:
        ticker: Stock symbol
        interval: Data interval ('1m', '5m', '15m', '30m', '1h')
        days: Number of days to fetch
        
    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"Fetching {interval} data for {ticker} ({days} days)")
    
    # yfinance limits: 1m data for last 7 days, 5m for 60 days
    if interval == '1m':
        period = f"{min(days, 7)}d"
    elif interval == '5m':
        period = f"{min(days, 60)}d"
    else:
        period = f"{days}d"
    
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            raise ValueError(f"No data returned for {ticker}")
        
        logger.info(f"Fetched {len(df)} bars from {df.index[0]} to {df.index[-1]}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise


def prepare_training_data(
    df: pd.DataFrame,
    horizons: Tuple[int, ...] = (5, 15),
    quantiles: Tuple[float, ...] = (0.1, 0.9)
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Prepare features and labels for training.
    
    Args:
        df: Raw OHLCV data
        horizons: Prediction horizons in bars
        quantiles: Quantiles to predict
        
    Returns:
        Tuple of (features_df, labels_high_df, labels_low_df)
    """
    logger.info("Creating features...")
    features = make_intraday_features(df, include_session_context=True)
    
    # Validate no leakage in features
    validate_features_no_leakage(df, features, check_index=min(100, len(df) // 2))
    
    logger.info("Creating labels...")
    labels = create_training_labels(df, horizons=horizons, label_type='absolute')
    
    # Validate no leakage in labels
    for H in horizons:
        label_dict = {
            f'high_next_{H}m': labels[f'high_next_{H}m'],
            f'low_next_{H}m': labels[f'low_next_{H}m']
        }
        validate_no_leakage(df, label_dict, H)
    
    return features, labels


def walk_forward_split(
    df: pd.DataFrame,
    test_size: float = 0.2
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data using walk-forward (time-based) split.
    
    Args:
        df: DataFrame with DatetimeIndex
        test_size: Fraction of data for testing
        
    Returns:
        Tuple of (train_df, test_df)
    """
    split_idx = int(len(df) * (1 - test_size))
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    logger.info(f"Train: {len(train_df)} samples ({train_df.index[0]} to {train_df.index[-1]})")
    logger.info(f"Test: {len(test_df)} samples ({test_df.index[0]} to {test_df.index[-1]})")
    
    return train_df, test_df


def train_bounds_model(
    ticker: str,
    interval: str = '1m',
    horizons: Tuple[int, ...] = (5, 15),
    days: int = 30,
    quantiles: Tuple[float, ...] = (0.1, 0.9),
    model_type: str = 'xgboost',
    test_size: float = 0.2,
    save_path: Path = None
) -> dict:
    """
    Train intraday bounds prediction model.
    
    Args:
        ticker: Stock symbol
        interval: Data interval
        horizons: Prediction horizons
        days: Days of historical data
        quantiles: Quantiles to predict
        model_type: Model type ('xgboost', 'lightgbm', 'ridge')
        test_size: Test set fraction
        save_path: Path to save model
        
    Returns:
        Dict with training results
    """
    # Fetch data
    df = fetch_intraday_data(ticker, interval, days)
    
    # Prepare features and labels
    features, labels = prepare_training_data(df, horizons, quantiles)
    
    results = {}
    
    # Train model for each horizon
    for H in horizons:
        logger.info(f"\n{'='*60}")
        logger.info(f"Training model for horizon={H} bars")
        logger.info(f"{'='*60}")
        
        # Get labels for this horizon
        high_label = f'high_next_{H}m'
        low_label = f'low_next_{H}m'
        
        # Combine features and labels
        combined = pd.concat([features, labels[[high_label, low_label]]], axis=1)
        combined = combined.dropna()  # Remove rows with NaN labels
        
        logger.info(f"Valid samples after removing NaN: {len(combined)}")
        
        # Split data
        train_df, test_df = walk_forward_split(combined, test_size=test_size)
        
        X_train = train_df[features.columns]
        X_test = test_df[features.columns]
        
        # Train HIGH model
        logger.info(f"\nTraining HIGH model (quantiles={quantiles})")
        y_train_high = train_df[high_label]
        y_test_high = test_df[high_label]
        
        model_high = fit_quantile_model(X_train, y_train_high, quantiles, model_type)
        
        metrics_high = evaluate_quantile_model(
            model_high,
            X_test,
            y_test_high,
            current_prices=test_df['Close'].values if 'Close' in test_df.columns else None
        )
        
        logger.info(f"HIGH model metrics: {metrics_high}")
        
        # Train LOW model
        logger.info(f"\nTraining LOW model (quantiles={quantiles})")
        y_train_low = train_df[low_label]
        y_test_low = test_df[low_label]
        
        model_low = fit_quantile_model(X_train, y_train_low, quantiles, model_type)
        
        metrics_low = evaluate_quantile_model(
            model_low,
            X_test,
            y_test_low,
            current_prices=test_df['Close'].values if 'Close' in test_df.columns else None
        )
        
        logger.info(f"LOW model metrics: {metrics_low}")
        
        # Save models
        if save_path:
            timestamp = datetime.now().strftime("%Y%m%d")
            
            high_path = save_path / f"intraday_bounds_{ticker}_{interval}_high_{H}bars_{timestamp}.joblib"
            low_path = save_path / f"intraday_bounds_{ticker}_{interval}_low_{H}bars_{timestamp}.joblib"
            
            metadata = {
                'ticker': ticker,
                'interval': interval,
                'horizon': H,
                'quantiles': quantiles,
                'model_type': model_type,
                'trained_at': datetime.now().isoformat(),
                'n_train': len(X_train),
                'n_test': len(X_test),
                'feature_names': list(features.columns)
            }
            
            save_model(model_high, high_path, {**metadata, 'target': 'high', 'metrics': metrics_high})
            save_model(model_low, low_path, {**metadata, 'target': 'low', 'metrics': metrics_low})
            
            logger.info(f"✅ Models saved to {save_path}")
        
        results[f'horizon_{H}'] = {
            'high_metrics': metrics_high,
            'low_metrics': metrics_low,
            'n_train': len(X_train),
            'n_test': len(X_test)
        }
    
    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Train intraday bounds prediction model')
    parser.add_argument('--ticker', type=str, required=True, help='Stock ticker symbol')
    parser.add_argument('--interval', type=str, default='1m', choices=['1m', '5m', '15m', '30m', '1h'],
                        help='Data interval')
    parser.add_argument('--horizons', type=int, nargs='+', default=[5, 15],
                        help='Prediction horizons in bars')
    parser.add_argument('--days', type=int, default=30, help='Days of historical data')
    parser.add_argument('--quantiles', type=float, nargs='+', default=[0.1, 0.9],
                        help='Quantiles to predict')
    parser.add_argument('--model-type', type=str, default='xgboost', choices=['xgboost', 'lightgbm', 'ridge'],
                        help='Model type')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set fraction')
    parser.add_argument('--save-dir', type=str, default='backend/app/ml/artifacts',
                        help='Directory to save models')
    
    args = parser.parse_args()
    
    # Convert to Path
    save_path = Path(args.save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Train
    results = train_bounds_model(
        ticker=args.ticker,
        interval=args.interval,
        horizons=tuple(args.horizons),
        days=args.days,
        quantiles=tuple(args.quantiles),
        model_type=args.model_type,
        test_size=args.test_size,
        save_path=save_path
    )
    
    # Print summary
    print("\n" + "="*60)
    print("TRAINING SUMMARY")
    print("="*60)
    for horizon_key, metrics in results.items():
        print(f"\n{horizon_key}:")
        print(f"  Train samples: {metrics['n_train']}")
        print(f"  Test samples: {metrics['n_test']}")
        print(f"  HIGH coverage: {metrics['high_metrics'].get('coverage', 0):.2%}")
        print(f"  LOW coverage: {metrics['low_metrics'].get('coverage', 0):.2%}")
        print(f"  HIGH band width: {metrics['high_metrics'].get('avg_band_width', 0):.2f}")
        print(f"  LOW band width: {metrics['low_metrics'].get('avg_band_width', 0):.2f}")


if __name__ == '__main__':
    main()

