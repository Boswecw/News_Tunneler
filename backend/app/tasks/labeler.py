"""
Signal labeling task.

Labels signals with forward returns for ML training.
"""
import logging
from datetime import datetime, timedelta
from app.core.db import get_db_context
from app.models.signal import Signal
from app.services.prices import get_close, index_ret

logger = logging.getLogger(__name__)


def label_signals(index_symbol: str = "^GSPC") -> int:
    """
    Label unlabeled signals with forward returns.
    
    For each signal without labels:
    1. Fetch closing price at signal time (t)
    2. Fetch closing price 1 day later (t+1d)
    3. Calculate return: (p1/p0) - 1
    4. Calculate index return for same period
    5. Set y_beat = 1 if stock beat index, else 0
    
    Args:
        index_symbol: Index ticker for comparison (default: ^GSPC for S&P 500)
        
    Returns:
        Number of signals labeled
    """
    logger.info(f"Starting signal labeling (index: {index_symbol})")
    
    with get_db_context() as db:
        # Find unlabeled signals
        unlabeled = db.query(Signal).filter(Signal.y_beat.is_(None)).all()
        
        if not unlabeled:
            logger.info("No unlabeled signals found")
            return 0
        
        logger.info(f"Found {len(unlabeled)} unlabeled signals")
        
        labeled_count = 0
        
        for signal in unlabeled:
            try:
                # Convert timestamp to datetime
                t0 = datetime.fromtimestamp(signal.t / 1000)
                t1 = t0 + timedelta(days=1)
                
                # Fetch prices
                p0 = get_close(signal.symbol, t0)
                p1 = get_close(signal.symbol, t1)
                
                if p0 is None or p1 is None:
                    logger.warning(f"Could not fetch prices for {signal.symbol} at {t0.date()}")
                    continue
                
                # Calculate stock return
                stock_ret = (p1 / p0) - 1.0
                
                # Calculate index return
                idx_ret = index_ret(index_symbol, t0, t1)
                
                # Label
                signal.y_ret_1d = stock_ret
                signal.y_beat = 1 if stock_ret > idx_ret else 0
                
                db.add(signal)
                labeled_count += 1
                
                logger.debug(
                    f"Labeled {signal.symbol} @ {t0.date()}: "
                    f"ret={stock_ret*100:.2f}%, idx={idx_ret*100:.2f}%, "
                    f"beat={signal.y_beat}"
                )
                
            except Exception as e:
                logger.error(f"Error labeling signal {signal.id}: {e}")
                continue
        
        db.commit()
        
        logger.info(f"Successfully labeled {labeled_count} signals")
        return labeled_count

