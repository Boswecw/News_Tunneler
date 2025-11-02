"""
Backtesting for Intraday Bounds Prediction

Evaluates model performance on historical data with walk-forward validation.

Usage:
    python -m backend.app.ml.backtest_bounds --ticker AAPL --interval 1m --horizon 5
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np

from app.ml.train_intraday_bounds import fetch_intraday_data, prepare_training_data
from app.ml.intraday_models import load_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backtest_model(
    ticker: str,
    interval: str,
    horizon: int,
    model_high_path: Path,
    model_low_path: Path,
    days: int = 30
) -> pd.DataFrame:
    """
    Backtest bounds prediction model.
    
    Args:
        ticker: Stock symbol
        interval: Data interval
        horizon: Prediction horizon
        model_high_path: Path to HIGH model
        model_low_path: Path to LOW model
        days: Days of data to backtest
        
    Returns:
        DataFrame with backtest results per bar
    """
    logger.info(f"Loading models...")
    model_high, metadata_high = load_model(model_high_path)
    model_low, metadata_low = load_model(model_low_path)
    
    logger.info(f"Fetching data...")
    df = fetch_intraday_data(ticker, interval, days)
    
    logger.info(f"Preparing features...")
    features, labels = prepare_training_data(df, horizons=(horizon,))
    
    # Combine
    high_label = f'high_next_{horizon}m'
    low_label = f'low_next_{horizon}m'
    
    combined = pd.concat([features, labels[[high_label, low_label]]], axis=1)
    combined = combined.dropna()
    
    logger.info(f"Backtesting on {len(combined)} bars...")
    
    # Get features
    X = combined[features.columns]
    
    # Predict
    pred_high = model_high.predict(X)
    pred_low = model_low.predict(X)
    
    # Get quantiles (assume 0.1 and 0.9)
    quantiles = sorted(pred_high.keys())
    lower_q = quantiles[0]
    upper_q = quantiles[-1]
    
    # Create results DataFrame
    results = pd.DataFrame({
        'timestamp': combined.index,
        'actual_high': combined[high_label],
        'actual_low': combined[low_label],
        'pred_high_lower': pred_high[lower_q],
        'pred_high_upper': pred_high[upper_q],
        'pred_low_lower': pred_low[lower_q],
        'pred_low_upper': pred_low[upper_q],
    })
    
    # Add current price if available
    if 'Close' in df.columns:
        results['current_price'] = df.loc[combined.index, 'Close'].values
    
    # Calculate metrics per bar
    results['high_within_band'] = (
        (results['actual_high'] >= results['pred_high_lower']) &
        (results['actual_high'] <= results['pred_high_upper'])
    )
    
    results['low_within_band'] = (
        (results['actual_low'] >= results['pred_low_lower']) &
        (results['actual_low'] <= results['pred_low_upper'])
    )
    
    results['high_band_width'] = results['pred_high_upper'] - results['pred_high_lower']
    results['low_band_width'] = results['pred_low_upper'] - results['pred_low_lower']
    
    if 'current_price' in results.columns:
        results['high_band_width_pct'] = (results['high_band_width'] / results['current_price']) * 100
        results['low_band_width_pct'] = (results['low_band_width'] / results['current_price']) * 100
    
    # Violations (actual outside band)
    results['high_violation'] = ~results['high_within_band']
    results['low_violation'] = ~results['low_within_band']
    
    return results


def compute_summary_metrics(results: pd.DataFrame) -> Dict:
    """Compute summary metrics from backtest results."""
    metrics = {
        'total_bars': len(results),
        'high_coverage': results['high_within_band'].mean(),
        'low_coverage': results['low_within_band'].mean(),
        'high_violation_rate': results['high_violation'].mean(),
        'low_violation_rate': results['low_violation'].mean(),
        'avg_high_band_width': results['high_band_width'].mean(),
        'avg_low_band_width': results['low_band_width'].mean(),
    }
    
    if 'high_band_width_pct' in results.columns:
        metrics['avg_high_band_width_pct'] = results['high_band_width_pct'].mean()
        metrics['avg_low_band_width_pct'] = results['low_band_width_pct'].mean()
    
    return metrics


def compute_time_bucket_metrics(results: pd.DataFrame) -> pd.DataFrame:
    """Compute metrics by time of day."""
    results = results.copy()
    results['hour'] = results['timestamp'].dt.hour
    results['minute_bucket'] = (results['timestamp'].dt.hour * 60 + results['timestamp'].dt.minute) // 30
    
    bucket_metrics = results.groupby('minute_bucket').agg({
        'high_within_band': 'mean',
        'low_within_band': 'mean',
        'high_band_width': 'mean',
        'low_band_width': 'mean',
        'high_violation': 'sum',
        'low_violation': 'sum',
    }).rename(columns={
        'high_within_band': 'high_coverage',
        'low_within_band': 'low_coverage',
        'high_violation': 'high_violations',
        'low_violation': 'low_violations',
    })
    
    return bucket_metrics


def save_backtest_results(
    results: pd.DataFrame,
    summary: Dict,
    ticker: str,
    interval: str,
    horizon: int,
    output_dir: Path
) -> None:
    """Save backtest results to CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed results
    results_path = output_dir / f"{ticker}_{interval}_h{horizon}_{timestamp}_results.csv"
    results.to_csv(results_path, index=False)
    logger.info(f"Detailed results saved to {results_path}")
    
    # Save summary
    summary_path = output_dir / f"{ticker}_{interval}_h{horizon}_{timestamp}_summary.csv"
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(summary_path, index=False)
    logger.info(f"Summary saved to {summary_path}")
    
    # Save time bucket metrics
    bucket_metrics = compute_time_bucket_metrics(results)
    bucket_path = output_dir / f"{ticker}_{interval}_h{horizon}_{timestamp}_buckets.csv"
    bucket_metrics.to_csv(bucket_path)
    logger.info(f"Time bucket metrics saved to {bucket_path}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Backtest intraday bounds prediction model')
    parser.add_argument('--ticker', type=str, required=True, help='Stock ticker symbol')
    parser.add_argument('--interval', type=str, default='1m', help='Data interval')
    parser.add_argument('--horizon', type=int, default=5, help='Prediction horizon in bars')
    parser.add_argument('--days', type=int, default=30, help='Days to backtest')
    parser.add_argument('--model-dir', type=str, default='backend/app/ml/artifacts',
                        help='Directory containing models')
    parser.add_argument('--output-dir', type=str, default='backend/data/backtests',
                        help='Directory to save results')
    
    args = parser.parse_args()
    
    # Find model files
    model_dir = Path(args.model_dir)
    
    # Look for most recent models
    high_models = list(model_dir.glob(f"intraday_bounds_{args.ticker}_{args.interval}_high_{args.horizon}bars_*.joblib"))
    low_models = list(model_dir.glob(f"intraday_bounds_{args.ticker}_{args.interval}_low_{args.horizon}bars_*.joblib"))
    
    if not high_models or not low_models:
        logger.error(f"No models found in {model_dir} for {args.ticker} {args.interval} horizon={args.horizon}")
        logger.error(f"Expected pattern: intraday_bounds_{args.ticker}_{args.interval}_{{high|low}}_{args.horizon}bars_*.joblib")
        return
    
    # Use most recent
    model_high_path = sorted(high_models)[-1]
    model_low_path = sorted(low_models)[-1]
    
    logger.info(f"Using HIGH model: {model_high_path.name}")
    logger.info(f"Using LOW model: {model_low_path.name}")
    
    # Run backtest
    results = backtest_model(
        ticker=args.ticker,
        interval=args.interval,
        horizon=args.horizon,
        model_high_path=model_high_path,
        model_low_path=model_low_path,
        days=args.days
    )
    
    # Compute summary
    summary = compute_summary_metrics(results)
    
    # Save results
    output_dir = Path(args.output_dir)
    save_backtest_results(results, summary, args.ticker, args.interval, args.horizon, output_dir)
    
    # Print summary
    print("\n" + "="*60)
    print("BACKTEST SUMMARY")
    print("="*60)
    print(f"Ticker: {args.ticker}")
    print(f"Interval: {args.interval}")
    print(f"Horizon: {args.horizon} bars")
    print(f"Total bars: {summary['total_bars']}")
    print(f"\nHIGH Predictions:")
    print(f"  Coverage: {summary['high_coverage']:.2%}")
    print(f"  Violation rate: {summary['high_violation_rate']:.2%}")
    print(f"  Avg band width: ${summary['avg_high_band_width']:.2f}")
    if 'avg_high_band_width_pct' in summary:
        print(f"  Avg band width %: {summary['avg_high_band_width_pct']:.2f}%")
    print(f"\nLOW Predictions:")
    print(f"  Coverage: {summary['low_coverage']:.2%}")
    print(f"  Violation rate: {summary['low_violation_rate']:.2%}")
    print(f"  Avg band width: ${summary['avg_low_band_width']:.2f}")
    if 'avg_low_band_width_pct' in summary:
        print(f"  Avg band width %: {summary['avg_low_band_width_pct']:.2f}%")


if __name__ == '__main__':
    main()

