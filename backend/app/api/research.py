"""
Research API endpoints for self-training ML predictions.

Provides:
- Model predictions for article analysis
- Human feedback for active learning
- Model metrics and status
"""
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml.features import featurize, validate_features
from app.ml.model import predict_proba, learn_and_save, get_metrics
from app.core.logging import logger


router = APIRouter(prefix="/research", tags=["research"])


class PredictRequest(BaseModel):
    """Request for model prediction."""
    analysis: Dict[str, Any] = Field(
        ...,
        description="Analysis payload with technical indicators and LLM outputs"
    )


class PredictResponse(BaseModel):
    """Response with model prediction."""
    prob_up_3d: float = Field(
        ...,
        description="Probability of positive 3-day return",
        ge=0.0,
        le=1.0
    )
    model_version: str = Field(
        default="rsm-v1",
        description="Model version identifier"
    )
    confidence: str = Field(
        ...,
        description="Human-readable confidence level"
    )


class FeedbackRequest(BaseModel):
    """Request for human feedback."""
    analysis: Dict[str, Any] = Field(
        ...,
        description="Analysis payload"
    )
    label: int = Field(
        ...,
        description="Human label: 0 (negative) or 1 (positive)",
        ge=0,
        le=1
    )


class MetricsResponse(BaseModel):
    """Model metrics response."""
    n_samples: int = Field(..., description="Number of training samples")
    log_loss: float | None = Field(None, description="Log loss (lower is better)")
    model_version: str = Field(..., description="Model version")


@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Get model prediction for article analysis.
    
    Returns probability that the stock will have a positive
    3-day return (>1%) based on the analysis features.
    """
    try:
        # Extract features
        features = featurize(request.analysis)
        
        # Validate features
        if not validate_features(features):
            raise HTTPException(
                status_code=400,
                detail="Insufficient features for prediction. Need both numeric and categorical features."
            )
        
        # Get prediction
        prob = predict_proba(features)
        
        # Determine confidence level
        if prob >= 0.7:
            confidence = "High"
        elif prob >= 0.55:
            confidence = "Moderate"
        elif prob >= 0.45:
            confidence = "Neutral"
        elif prob >= 0.3:
            confidence = "Low"
        else:
            confidence = "Very Low"
        
        return PredictResponse(
            prob_up_3d=prob,
            model_version="rsm-v1",
            confidence=confidence
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/feedback")
async def feedback(request: FeedbackRequest):
    """
    Submit human feedback for active learning.
    
    Allows users to provide labels for articles, which
    immediately updates the model.
    """
    try:
        # Extract features
        features = featurize(request.analysis)
        
        # Validate features
        if not validate_features(features):
            raise HTTPException(
                status_code=400,
                detail="Insufficient features for training"
            )
        
        # Train model
        learn_and_save(features, request.label)
        
        logger.info(f"Received human feedback: label={request.label}")
        
        return {
            "ok": True,
            "message": "Feedback received and model updated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Feedback processing failed: {str(e)}"
        )


@router.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """
    Get current model metrics.
    
    Returns training statistics and performance metrics.
    """
    try:
        metrics_data = get_metrics()
        return MetricsResponse(**metrics_data)
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.get("/health")
async def health():
    """Health check for research service."""
    return {
        "status": "ok",
        "service": "research",
        "version": "rsm-v1"
    }

