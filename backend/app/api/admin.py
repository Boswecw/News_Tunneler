"""
Admin API Endpoints

Provides administrative functions like model training and feature flag management.
"""
from fastapi import APIRouter, HTTPException, Request, Header, Query
from typing import Dict, List, Optional
from app.tasks.labeler import label_signals
from app.train.train_signals import train_model
from app.core.logging import logger
from app.middleware.rate_limit import limiter
from app.core.feature_flags import get_feature_flags, FeatureFlag
from app.core.memory_cache import get_memory_cache, invalidate_opportunities, invalidate_model_registry
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


@router.get("/cache/stats")
@limiter.limit("60/minute")
def get_cache_stats(request: Request) -> Dict:
    """
    Get memory cache statistics.

    Returns:
        {
            "status": "active",
            "entries": int,
            "hits": int,
            "misses": int,
            "hit_rate": str,
            "total_requests": int
        }
    """
    try:
        cache = get_memory_cache()
        stats = cache.stats()
        logger.info(f"Admin: Cache stats requested - {stats['hit_rate']} hit rate")
        return stats
    except Exception as e:
        logger.error(f"Admin: Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
@limiter.limit("10/hour")
def clear_cache(request: Request) -> Dict:
    """
    Clear all memory cache entries.

    Returns:
        {
            "ok": bool,
            "message": str
        }
    """
    try:
        cache = get_memory_cache()
        cache.clear()
        logger.info("Admin: Memory cache cleared")
        return {
            "ok": True,
            "message": "Memory cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Admin: Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate/opportunities")
@limiter.limit("30/hour")
def invalidate_opportunities_cache(request: Request) -> Dict:
    """
    Invalidate opportunities cache.

    Returns:
        {
            "ok": bool,
            "message": str
        }
    """
    try:
        invalidate_opportunities()
        logger.info("Admin: Opportunities cache invalidated")
        return {
            "ok": True,
            "message": "Opportunities cache invalidated successfully"
        }
    except Exception as e:
        logger.error(f"Admin: Error invalidating opportunities cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate/models")
@limiter.limit("30/hour")
def invalidate_models_cache(request: Request) -> Dict:
    """
    Invalidate model registry cache.

    Returns:
        {
            "ok": bool,
            "message": str
        }
    """
    try:
        invalidate_model_registry()
        logger.info("Admin: Model registry cache invalidated")
        return {
            "ok": True,
            "message": "Model registry cache invalidated successfully"
        }
    except Exception as e:
        logger.error(f"Admin: Error invalidating model registry cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/send-opportunities")
@limiter.limit("10/hour")
def trigger_opportunities_report(
    request: Request,
    session: str = Query("pre-market", regex="^(pre-market|mid-day|after-close)$"),
    force: bool = Query(False),
    admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
) -> Dict:
    """
    Manually trigger daily opportunities email report.

    Args:
        session: Trading session label (pre-market, mid-day, after-close)
        force: Force send even if already sent today
        admin_token: Admin authentication token (X-Admin-Token header)

    Returns:
        {
            "status": "sent",
            "report_id": str,
            "candidates_count": int,
            "recipients": list[str]
        }

    Raises:
        401: Invalid or missing admin token
        400: No recipients configured
        500: Failed to send report
    """
    try:
        from app.core.config import get_settings
        from app.services.mailer import send_top_opportunities_report

        settings = get_settings()

        # Validate admin token
        if not settings.admin_token or admin_token != settings.admin_token:
            logger.warning("Admin: Unauthorized report trigger attempt")
            raise HTTPException(status_code=401, detail="Invalid or missing admin token")

        # Check recipients configured
        recipients = settings.report_recipients
        if not recipients:
            raise HTTPException(status_code=400, detail="No recipients configured (REPORT_RECIPIENTS)")

        # Map session parameter to label
        session_map = {
            "pre-market": "Pre-Market",
            "mid-day": "Mid-Day",
            "after-close": "After-Close"
        }
        session_label = session_map[session]

        logger.info(f"Admin: Manually triggering opportunities report ({session_label}, force={force})")

        # Send report
        result = send_top_opportunities_report(
            recipients=recipients,
            session_label=session_label,
            force=force
        )

        if result.get("success"):
            logger.info(f"Admin: Report sent successfully - {result['report_id']}")
            return {
                "status": "sent",
                "report_id": result["report_id"],
                "candidates_count": result["candidates_count"],
                "recipients": result["recipients"],
            }
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Admin: Report failed - {error_msg}")
            raise HTTPException(status_code=500, detail=f"Failed to send report: {error_msg}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin: Error triggering opportunities report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

