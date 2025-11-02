"""
Training API Endpoints

Provides endpoints for training price prediction models, making predictions,
and managing model artifacts.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import pathlib
import pandas as pd
import yfinance as yf
from sqlalchemy import text
import asyncio

from app.core.db import get_db_context
from app.core.logging import logger
from app.ml.price_model import (
    calculate_indicators,
    compute_time_decay_weights,
    prepare_features_and_target,
    train_model,
    evaluate_model,
    save_model,
    load_model
)
from app.services.model_registry import ModelRegistry, ModelMetadata


router = APIRouter(prefix="/api/training", tags=["training"])

# Configuration
MODEL_DIR = pathlib.Path("models")
REGISTRY_PATH = MODEL_DIR / "registry.json"
ARCHIVE_DIR = MODEL_DIR / "archives"

# Initialize registry
registry = ModelRegistry(REGISTRY_PATH)


class TrainResponse(BaseModel):
    """Response from training endpoint."""
    ticker: str
    mode: str
    model_path: str
    r2_score: float
    n_observations: int
    trained_at: str
    param_hash: str
    archive_path: Optional[str] = None
    pruned_rows: int


class PredictResponse(BaseModel):
    """Response from predict endpoint."""
    ticker: str
    mode: str
    predicted_close: float
    current_close: float
    predicted_change_pct: float
    model_trained_at: str
    features_snapshot: Dict[str, Any]


class PruneResponse(BaseModel):
    """Response from prune endpoint."""
    pruned_rows: int
    retained_rows: int
    vacuum_completed: bool


class ModelListResponse(BaseModel):
    """Response from models list endpoint."""
    models: List[ModelMetadata]
    total_count: int


def _download_historical_data(ticker: str, mode: str) -> pd.DataFrame:
    """
    Download historical price data from yfinance.

    Args:
        ticker: Stock ticker symbol
        mode: Training mode ("5y" or "10y")

    Returns:
        DataFrame with OHLCV data
    """
    period = "5y" if mode == "5y" else "10y"

    logger.info(f"Downloading {period} historical data for {ticker}")
    df = yf.download(ticker, period=period, progress=False)

    if df.empty:
        raise ValueError(f"No data available for ticker {ticker}")

    # Flatten MultiIndex columns if present (yfinance returns MultiIndex for single ticker)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Reset index to make Date a column
    df = df.reset_index()

    # Ensure we have required columns
    required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    return df


def _store_historical_data(ticker: str, df: pd.DataFrame) -> int:
    """
    Store historical data in database.
    
    Args:
        ticker: Stock ticker symbol
        df: DataFrame with historical data
        
    Returns:
        Number of rows inserted
    """
    with get_db_context() as db:
        # Create table if not exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS historical_prices (
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (ticker, date)
            )
        """))
        db.commit()
        
        # Insert data
        rows_inserted = 0
        for _, row in df.iterrows():
            # Convert Date to string - handle both Timestamp and datetime objects
            date_val = row["Date"]
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val)[:10]  # Take first 10 chars (YYYY-MM-DD)

            db.execute(text("""
                INSERT OR REPLACE INTO historical_prices
                (ticker, date, open, high, low, close, volume)
                VALUES (:ticker, :date, :open, :high, :low, :close, :volume)
            """), {
                "ticker": ticker,
                "date": date_str,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })
            rows_inserted += 1
        
        db.commit()
    
    return rows_inserted


def _prune_historical_data(
    ticker: Optional[str],
    retain: Literal["none", "window", "all"],
    window_days: int
) -> int:
    """
    Prune historical data according to retention policy.
    
    Args:
        ticker: Optional ticker to prune (None = all tickers)
        retain: Retention policy
        window_days: Number of days to retain if retain="window"
        
    Returns:
        Number of rows deleted
    """
    with get_db_context() as db:
        if retain == "none":
            # Delete all data for ticker
            if ticker:
                result = db.execute(
                    text("DELETE FROM historical_prices WHERE ticker = :ticker"),
                    {"ticker": ticker}
                )
            else:
                result = db.execute(text("DELETE FROM historical_prices"))
            
            db.commit()
            return result.rowcount
        
        elif retain == "window":
            # Keep only recent window_days
            cutoff_date = (datetime.now() - timedelta(days=window_days)).strftime("%Y-%m-%d")
            
            if ticker:
                result = db.execute(
                    text("DELETE FROM historical_prices WHERE ticker = :ticker AND date < :cutoff"),
                    {"ticker": ticker, "cutoff": cutoff_date}
                )
            else:
                result = db.execute(
                    text("DELETE FROM historical_prices WHERE date < :cutoff"),
                    {"cutoff": cutoff_date}
                )
            
            db.commit()
            return result.rowcount
        
        else:  # retain == "all"
            return 0


def _vacuum_database() -> None:
    """Run VACUUM to reclaim space after pruning."""
    with get_db_context() as db:
        db.execute(text("VACUUM"))
        db.commit()


@router.post("/train/{ticker}", response_model=TrainResponse)
async def train_ticker(
    ticker: str,
    mode: Literal["5y", "10y"] = Query("10y", description="Training mode"),
    retain: Literal["none", "window", "all"] = Query("none", description="Data retention policy"),
    window_days: int = Query(180, description="Days to retain if retain=window"),
    archive: bool = Query(False, description="Archive training data to Parquet")
) -> TrainResponse:
    """
    Train price prediction model for a ticker.

    Downloads historical data, trains model, saves artifacts, and applies retention policy.
    """
    try:
        # Download historical data (blocking I/O - run in thread)
        df = await asyncio.to_thread(_download_historical_data, ticker, mode)
        logger.info(f"Downloaded {len(df)} rows for {ticker}")

        # Store in database (blocking I/O - run in thread)
        rows_inserted = await asyncio.to_thread(_store_historical_data, ticker, df)
        logger.info(f"Stored {rows_inserted} rows in database")

        # Calculate indicators
        indicator_config = {
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

        # Calculate indicators (CPU-intensive - run in thread)
        df_with_indicators = await asyncio.to_thread(
            calculate_indicators, df.set_index("Date"), indicator_config
        )

        # Prepare features and target (CPU-intensive - run in thread)
        X, y = await asyncio.to_thread(prepare_features_and_target, df_with_indicators)
        logger.info(f"Prepared {len(X)} samples with {X.shape[1]} features")

        # Compute time-decay weights for 10y mode
        sample_weights = None
        if mode == "10y":
            sample_weights = await asyncio.to_thread(
                compute_time_decay_weights, X, half_life_days=365
            )

        # Train model (CPU-intensive - run in thread)
        model = await asyncio.to_thread(
            train_model, X, y, mode=mode, sample_weights=sample_weights
        )

        # Evaluate model (CPU-intensive - run in thread)
        metrics = await asyncio.to_thread(evaluate_model, model, X, y)
        logger.info(f"Model R²: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.4f}")

        # Save model (blocking I/O - run in thread)
        model_path = MODEL_DIR / f"{ticker}_{mode}.pkl"
        await asyncio.to_thread(save_model, model, model_path, compress=3)
        logger.info(f"Saved model to {model_path}")

        # Archive data if requested
        archive_path = None
        if archive:
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            archive_path = ARCHIVE_DIR / f"{ticker}_{mode}_{datetime.now().strftime('%Y-%m-%d')}.parquet.gz"
            await asyncio.to_thread(df.to_parquet, archive_path, compression="gzip")
            logger.info(f"Archived data to {archive_path}")

        # Add to registry
        # Convert dates to strings safely
        date_min = df["Date"].min()
        date_max = df["Date"].max()
        date_range_start = date_min.strftime("%Y-%m-%d") if hasattr(date_min, 'strftime') else str(date_min)[:10]
        date_range_end = date_max.strftime("%Y-%m-%d") if hasattr(date_max, 'strftime') else str(date_max)[:10]

        metadata = await asyncio.to_thread(
            registry.add_model,
            ticker=ticker,
            mode=mode,
            model_path=str(model_path),
            r2_score=metrics["r2"],
            n_observations=len(X),
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            indicator_config=indicator_config,
            archive_path=str(archive_path) if archive_path else None
        )

        # Prune historical data (blocking I/O - run in thread)
        pruned_rows = await asyncio.to_thread(_prune_historical_data, ticker, retain, window_days)
        logger.info(f"Pruned {pruned_rows} rows from database")

        # Vacuum database (blocking I/O - run in thread)
        await asyncio.to_thread(_vacuum_database)
        logger.info("Database vacuumed")
        
        return TrainResponse(
            ticker=ticker,
            mode=mode,
            model_path=str(model_path),
            r2_score=metrics["r2"],
            n_observations=len(X),
            trained_at=metadata.trained_at,
            param_hash=metadata.param_hash,
            archive_path=str(archive_path) if archive_path else None,
            pruned_rows=pruned_rows
        )
    
    except Exception as e:
        logger.error(f"Error training model for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/{ticker}", response_model=PredictResponse)
async def predict_ticker(
    ticker: str,
    mode: Literal["5y", "10y"] = Query("10y", description="Model mode to use")
) -> PredictResponse:
    """
    Get price prediction for a ticker using trained model.

    Returns next-day close price prediction and feature snapshot.
    """
    try:
        # Get model metadata from registry
        metadata = registry.get_model(ticker, mode)
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"No trained model found for {ticker} with mode {mode}"
            )

        # Load model
        model_path = pathlib.Path(metadata.model_path)
        if not model_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Model file not found: {model_path}"
            )

        # Load model (blocking I/O - run in thread)
        model = await asyncio.to_thread(load_model, model_path)

        # Download recent data for prediction (blocking I/O - run in thread)
        df = await asyncio.to_thread(yf.download, ticker, period="3mo", progress=False)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No recent data for {ticker}")

        df = df.reset_index()

        # Calculate indicators (CPU-intensive - run in thread)
        df_with_indicators = await asyncio.to_thread(
            calculate_indicators, df.set_index("Date"), metadata.indicator_config
        )

        # Prepare features (use most recent row)
        X, _ = await asyncio.to_thread(prepare_features_and_target, df_with_indicators)
        if len(X) == 0:
            raise HTTPException(status_code=500, detail="Insufficient data for prediction")

        # Get most recent features
        X_latest = X.iloc[[-1]]

        # Make prediction (CPU-intensive - run in thread)
        predicted_close = float((await asyncio.to_thread(model.predict, X_latest))[0])

        # Get current close
        current_close = float(df["Close"].iloc[-1])

        # Calculate predicted change
        predicted_change_pct = ((predicted_close - current_close) / current_close) * 100

        # Create features snapshot
        features_snapshot = X_latest.iloc[0].to_dict()

        return PredictResponse(
            ticker=ticker,
            mode=mode,
            predicted_close=predicted_close,
            current_close=current_close,
            predicted_change_pct=predicted_change_pct,
            model_trained_at=metadata.trained_at,
            features_snapshot=features_snapshot
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prune", response_model=PruneResponse)
async def prune_historical_data(
    retain: Literal["none", "window"] = Query("window", description="Retention policy"),
    window_days: int = Query(180, description="Days to retain if retain=window")
) -> PruneResponse:
    """
    Bulk prune historical data across all tickers.

    Applies retention policy and runs VACUUM to reclaim space.
    """
    try:
        # Count rows before pruning (blocking I/O - run in thread)
        def count_rows():
            with get_db_context() as db:
                result = db.execute(text("SELECT COUNT(*) FROM historical_prices"))
                return result.scalar()

        rows_before = await asyncio.to_thread(count_rows)

        # Prune data (blocking I/O - run in thread)
        pruned_rows = await asyncio.to_thread(_prune_historical_data, None, retain, window_days)

        # Count rows after pruning (blocking I/O - run in thread)
        rows_after = await asyncio.to_thread(count_rows)

        # Vacuum database (blocking I/O - run in thread)
        await asyncio.to_thread(_vacuum_database)

        logger.info(f"Pruned {pruned_rows} rows, {rows_after} rows remaining")

        return PruneResponse(
            pruned_rows=pruned_rows,
            retained_rows=rows_after,
            vacuum_completed=True
        )

    except Exception as e:
        logger.error(f"Error pruning data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=ModelListResponse)
async def list_models() -> ModelListResponse:
    """
    List all trained models in the registry.

    Returns metadata for all models including training metrics and parameters.
    """
    try:
        models = registry.list_models()

        return ModelListResponse(
            models=models,
            total_count=len(models)
        )

    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

