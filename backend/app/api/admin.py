"""
Admin API Endpoints

Provides administrative functions like model training and feature flag management.
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List
from app.tasks.labeler import label_signals
from app.train.train_signals import train_model
from app.core.logging import logger
from app.middleware.rate_limit import limiter
from app.core.feature_flags import get_feature_flags, FeatureFlag
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])


class FeatureFlagUpdate(BaseModel):
    """Schema for updating a feature flag."""
    flag_name: str
    enabled: bool


@router.post("/train")
@limiter.limit("5/hour")  # Rate limit: 5 requests per hour (expensive operation)
def trigger_training(request: Request) -> Dict:
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
@limiter.limit("5/hour")  # Rate limit: 5 requests per hour (expensive operation)
def trigger_labeling(request: Request, index_symbol: str = "^GSPC") -> Dict:
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


@router.get("/feature-flags")
@limiter.limit("10/minute")
def get_all_feature_flags(request: Request) -> Dict:
    """
    Get all feature flags and their current states.

    Returns:
        Dictionary of feature flags and their enabled/disabled states
    """
    try:
        flags = get_feature_flags()
        all_flags = flags.get_all()

        logger.info("Admin: Retrieved all feature flags")

        return {
            "ok": True,
            "flags": all_flags,
            "total": len(all_flags),
            "enabled_count": sum(1 for v in all_flags.values() if v)
        }
    except Exception as e:
        logger.error(f"Admin: Error retrieving feature flags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feature-flags")
@limiter.limit("5/hour")
def update_feature_flag(request: Request, update: FeatureFlagUpdate) -> Dict:
    """
    Update a feature flag's state.

    Args:
        update: Feature flag update payload

    Returns:
        Updated flag state
    """
    try:
        flags = get_feature_flags()

        # Validate flag name
        valid_flags = [f.value for f in FeatureFlag]
        if update.flag_name not in valid_flags:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid flag name. Valid flags: {', '.join(valid_flags)}"
            )

        # Update flag
        flags.set_flag(update.flag_name, update.enabled)

        logger.info(f"Admin: Updated feature flag {update.flag_name} = {update.enabled}")

        return {
            "ok": True,
            "flag_name": update.flag_name,
            "enabled": update.enabled
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin: Error updating feature flag: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feature-flags/{flag_name}/toggle")
@limiter.limit("5/hour")
def toggle_feature_flag(request: Request, flag_name: str) -> Dict:
    """
    Toggle a feature flag's state.

    Args:
        flag_name: Name of the feature flag to toggle

    Returns:
        New flag state
    """
    try:
        flags = get_feature_flags()

        # Validate flag name
        valid_flags = [f.value for f in FeatureFlag]
        if flag_name not in valid_flags:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid flag name. Valid flags: {', '.join(valid_flags)}"
            )

        # Toggle flag
        flag_enum = FeatureFlag(flag_name)
        new_state = flags.toggle(flag_enum)

        logger.info(f"Admin: Toggled feature flag {flag_name} = {new_state}")

        return {
            "ok": True,
            "flag_name": flag_name,
            "enabled": new_state
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin: Error toggling feature flag: {e}")
        raise HTTPException(status_code=500, detail=str(e))

