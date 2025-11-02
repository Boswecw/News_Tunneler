"""
Auto-labeling job for research model.

Automatically generates training labels from realized market returns
after sufficient time has passed to measure outcomes.
"""
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.research import ResearchFeatures, ResearchLabels
from app.core.prices import get_daily_prices
from app.ml.model import learn_and_save
from app.core.logging import logger


# Return threshold for positive label (1% gain over 3 trading days)
RET_THRESHOLD = 0.01

# Minimum days to wait before labeling (allows 3 trading days + buffer)
MIN_DAYS_WAIT = 7


def align_entry_dt(published_at: str) -> pd.Timestamp:
    """
    Align entry datetime to next tradeable session.
    
    Accounts for:
    - After-hours publications → next day open
    - Weekend publications → Monday open
    - Latency buffer
    
    Args:
        published_at: ISO8601 timestamp
        
    Returns:
        Pandas Timestamp of entry point
    """
    pub_dt = pd.Timestamp(published_at, tz='UTC')
    
    # Convert to ET for market hours check
    et_dt = pub_dt.tz_convert('America/New_York')
    
    # If published after 4 PM ET or on weekend, use next trading day
    if et_dt.hour >= 16 or et_dt.weekday() >= 5:
        # Add 1 day and align to next business day
        entry = (et_dt + pd.Timedelta(days=1)).floor('D')
        entry = entry + pd.tseries.offsets.BDay(0)  # Align to business day
    else:
        # Same day entry
        entry = et_dt.floor('D')
    
    return entry


def compute_label(
    symbol: str,
    published_at: str
) -> Optional[Tuple[int, float, str]]:
    """
    Compute label from realized returns.
    
    Args:
        symbol: Stock ticker
        published_at: ISO8601 publication timestamp
        
    Returns:
        Tuple of (label, return, entry_day) or None if insufficient data
    """
    try:
        # Determine entry point
        entry_dt = align_entry_dt(published_at)
        entry_day = entry_dt.floor('D')
        
        # Get historical prices
        df = get_daily_prices(symbol, use_cache=True)
        
        if df.empty:
            logger.warning(f"No price data for {symbol}")
            return None
        
        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Find entry price
        entry_prices = df[df['date'] == entry_day]
        if entry_prices.empty:
            # Try next available date
            entry_prices = df[df['date'] > entry_day].head(1)
            if entry_prices.empty:
                logger.warning(f"No entry price for {symbol} on {entry_day}")
                return None
        
        entry_price = float(entry_prices.iloc[0]['close'])
        actual_entry_day = entry_prices.iloc[0]['date']
        
        # Find exit price (3 trading days later)
        exit_day = actual_entry_day + pd.tseries.offsets.BDay(3)
        exit_prices = df[df['date'] >= exit_day].head(1)
        
        if exit_prices.empty:
            logger.warning(f"No exit price for {symbol} 3 days after {actual_entry_day}")
            return None
        
        exit_price = float(exit_prices.iloc[0]['close'])
        
        # Calculate return
        ret = (exit_price - entry_price) / entry_price
        
        # Generate binary label
        label = int(ret > RET_THRESHOLD)
        
        return label, ret, str(actual_entry_day.date())
        
    except Exception as e:
        logger.error(f"Error computing label for {symbol}: {e}")
        return None


def run(limit: int = 250):
    """
    Run auto-labeling job.
    
    Processes unlabeled articles that are old enough to have
    realized returns, generates labels, and trains model.
    
    Args:
        limit: Maximum number of articles to process
    """
    db = SessionLocal()
    
    try:
        # Calculate cutoff date (articles must be at least MIN_DAYS_WAIT old)
        cutoff = (datetime.utcnow() - timedelta(days=MIN_DAYS_WAIT)).isoformat()
        
        # Find unlabeled articles
        unlabeled = (
            db.query(ResearchFeatures)
            .filter(ResearchFeatures.published_at < cutoff)
            .filter(
                ~ResearchFeatures.article_id.in_(
                    db.query(ResearchLabels.article_id)
                )
            )
            .order_by(ResearchFeatures.published_at.asc())
            .limit(limit)
            .all()
        )
        
        logger.info(f"Found {len(unlabeled)} unlabeled articles to process")
        
        labeled_count = 0
        trained_count = 0
        
        for rf in unlabeled:
            # Compute label from realized returns
            result = compute_label(rf.symbol, rf.published_at)
            
            if result is None:
                continue
            
            label, ret_3d, entry_day = result
            
            # Parse features
            try:
                features = json.loads(rf.features_json)
            except json.JSONDecodeError:
                logger.error(f"Invalid features JSON for article {rf.article_id}")
                continue
            
            # Train model with this example
            try:
                learn_and_save(features, label)
                trained_count += 1
            except Exception as e:
                logger.error(f"Error training on article {rf.article_id}: {e}")
            
            # Store label
            label_row = ResearchLabels(
                article_id=rf.article_id,
                label=label,
                ret_3d=ret_3d,
                threshold=RET_THRESHOLD,
                entry_day=entry_day,
                created_at=datetime.utcnow().isoformat()
            )
            
            db.merge(label_row)
            labeled_count += 1
            
            # Commit in batches
            if labeled_count % 50 == 0:
                db.commit()
                logger.info(f"Processed {labeled_count} articles, trained on {trained_count}")
        
        # Final commit
        db.commit()
        
        logger.info(
            f"Auto-labeling complete: {labeled_count} labeled, {trained_count} trained"
        )
        
    except Exception as e:
        logger.error(f"Error in auto-labeling job: {e}")
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    # Allow running as standalone script
    run()

