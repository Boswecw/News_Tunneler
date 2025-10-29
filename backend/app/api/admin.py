"""
Admin API Endpoints

Provides administrative functions like model training.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
from app.tasks.labeler import label_signals
from app.train.train_signals import train_model
from app.core.logging import logger

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/train")
def trigger_training() -> Dict:
    """
    Trigger the ML training pipeline.
    
    Steps:
    1. Label unlabeled signals with forward returns
    2. Train logistic regression model on labeled data
    3. Save weights to data/model_weights.json
    4. Create ModelRun record
    
    Returns:
        {
            "ok": bool,
            "message": str,
            "labeled_count": int,
            "training_result": Dict or None
        }
    """
    try:
        logger.info("Admin: Starting training pipeline")
        
        # Step 1: Label signals
        labeled_count = label_signals(index_symbol="^GSPC")
        logger.info(f"Admin: Labeled {labeled_count} signals")
        
        # Step 2: Train model
        training_result = train_model(min_samples=50)
        
        if training_result is None:
            return {
                "ok": False,
                "message": "Insufficient labeled data for training (need at least 50 samples)",
                "labeled_count": labeled_count,
                "training_result": None,
            }
        
        logger.info(f"Admin: Training complete - {training_result['version']}")
        
        return {
            "ok": True,
            "message": "Training pipeline complete",
            "labeled_count": labeled_count,
            "training_result": training_result,
        }
        
    except Exception as e:
        logger.error(f"Admin: Training pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/label")
def trigger_labeling(index_symbol: str = "^GSPC") -> Dict:
    """
    Trigger signal labeling only (without training).
    
    Args:
        index_symbol: Index ticker for comparison (default: ^GSPC)
        
    Returns:
        {
            "ok": bool,
            "labeled_count": int
        }
    """
    try:
        logger.info(f"Admin: Starting labeling (index: {index_symbol})")
        
        labeled_count = label_signals(index_symbol=index_symbol)
        
        logger.info(f"Admin: Labeled {labeled_count} signals")
        
        return {
            "ok": True,
            "labeled_count": labeled_count,
        }
        
    except Exception as e:
        logger.error(f"Admin: Labeling error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

