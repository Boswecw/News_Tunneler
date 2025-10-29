"""
API endpoints for ML operations.

Provides endpoints for model training, prediction, comparison, and explainability.
"""
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.core.db import get_db_context
from app.models.ml_model import MLModel
from app.ml.training_pipeline import MLTrainingPipeline
from app.ml.advanced_models import AdvancedMLTrainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["ml"])


# Request/Response models
class TrainRequest(BaseModel):
    """Request model for training."""
    min_samples: int = 50
    model_types: Optional[List[str]] = None
    tune_hyperparams: bool = False
    use_feature_engineering: bool = True


class PredictRequest(BaseModel):
    """Request model for prediction."""
    features: Dict[str, float]
    model_version: Optional[str] = None


class PredictResponse(BaseModel):
    """Response model for prediction."""
    prediction: int
    probability: float
    model_version: str
    model_type: str


# Global trainer instance (loaded on demand)
_active_trainer: Optional[AdvancedMLTrainer] = None


def get_active_trainer() -> AdvancedMLTrainer:
    """
    Get or load the active ML model.
    
    Returns:
        AdvancedMLTrainer instance with loaded model
    """
    global _active_trainer
    
    if _active_trainer is None:
        # Load active model from database
        with get_db_context() as db:
            active_model = db.query(MLModel).filter(MLModel.is_active == True).first()
            
            if active_model is None:
                raise HTTPException(
                    status_code=404,
                    detail="No active ML model found. Please train a model first."
                )
            
            # Load model
            _active_trainer = AdvancedMLTrainer()
            _active_trainer.load_model(active_model.model_path)
            
            logger.info(f"Loaded active model: {active_model.version}")
    
    return _active_trainer


@router.post("/train")
async def train_models(request: TrainRequest, background_tasks: BackgroundTasks):
    """
    Train ML models on labeled signals.
    
    This endpoint runs the full training pipeline:
    1. Collect labeled signals from database
    2. Engineer features (if enabled)
    3. Train multiple model types
    4. Compare models and select best
    5. Save best model to database
    
    Training runs in the background to avoid timeout.
    """
    def run_training():
        try:
            logger.info("Starting ML training pipeline")
            
            # Create pipeline
            pipeline = MLTrainingPipeline(
                use_feature_engineering=request.use_feature_engineering,
                tune_hyperparams=request.tune_hyperparams
            )
            
            # Run pipeline
            results = pipeline.run_full_pipeline(
                min_samples=request.min_samples,
                model_types=request.model_types
            )
            
            logger.info(f"Training completed: {results['version']}")
            
            # Invalidate cached trainer
            global _active_trainer
            _active_trainer = None
        
        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
    
    # Run training in background
    background_tasks.add_task(run_training)
    
    return {
        "message": "Training started in background",
        "min_samples": request.min_samples,
        "model_types": request.model_types or ["random_forest", "xgboost", "lightgbm", "gradient_boosting"],
        "tune_hyperparams": request.tune_hyperparams,
        "use_feature_engineering": request.use_feature_engineering
    }


@router.get("/models")
def list_models(limit: int = 10, active_only: bool = False):
    """
    List trained ML models.
    
    Args:
        limit: Maximum number of models to return
        active_only: Only return active models
    """
    with get_db_context() as db:
        query = db.query(MLModel)
        
        if active_only:
            query = query.filter(MLModel.is_active == True)
        
        models = query.order_by(MLModel.created_at.desc()).limit(limit).all()
        
        return {
            "models": [
                {
                    "id": m.id,
                    "version": m.version,
                    "model_type": m.model_type,
                    "metrics": m.metrics,
                    "feature_importance": m.feature_importance,
                    "training_samples": m.training_samples,
                    "is_active": m.is_active,
                    "created_at": m.created_at.isoformat(),
                }
                for m in models
            ],
            "count": len(models)
        }


@router.get("/models/{version}")
def get_model(version: str):
    """
    Get details of a specific model.
    
    Args:
        version: Model version
    """
    with get_db_context() as db:
        model = db.query(MLModel).filter(MLModel.version == version).first()
        
        if model is None:
            raise HTTPException(status_code=404, detail=f"Model {version} not found")
        
        return {
            "id": model.id,
            "version": model.version,
            "model_type": model.model_type,
            "model_path": model.model_path,
            "metrics": model.metrics,
            "feature_importance": model.feature_importance,
            "hyperparameters": model.hyperparameters,
            "training_samples": model.training_samples,
            "is_active": model.is_active,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
        }


@router.post("/models/{version}/activate")
def activate_model(version: str):
    """
    Set a model as active for predictions.
    
    Args:
        version: Model version to activate
    """
    with get_db_context() as db:
        # Find model
        model = db.query(MLModel).filter(MLModel.version == version).first()
        
        if model is None:
            raise HTTPException(status_code=404, detail=f"Model {version} not found")
        
        # Deactivate all models
        db.query(MLModel).update({'is_active': False})
        
        # Activate this model
        model.is_active = True
        db.add(model)
        db.commit()
        
        # Invalidate cached trainer
        global _active_trainer
        _active_trainer = None
        
        logger.info(f"Activated model: {version}")
        
        return {
            "message": f"Model {version} activated",
            "version": version,
            "model_type": model.model_type
        }


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Make prediction using active ML model.
    
    Args:
        request: Prediction request with features
    """
    try:
        # Get active trainer
        trainer = get_active_trainer()
        
        # Make prediction
        prediction, probability = trainer.predict(request.features)
        
        # Get model info
        with get_db_context() as db:
            active_model = db.query(MLModel).filter(MLModel.is_active == True).first()
        
        return PredictResponse(
            prediction=prediction,
            probability=probability,
            model_version=active_model.version,
            model_type=active_model.model_type
        )
    
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch")
def predict_batch(features_list: List[Dict[str, float]]):
    """
    Make predictions for multiple feature sets.
    
    Args:
        features_list: List of feature dicts
    """
    try:
        # Get active trainer
        trainer = get_active_trainer()
        
        # Make predictions
        predictions = []
        for features in features_list:
            prediction, probability = trainer.predict(features)
            predictions.append({
                "prediction": prediction,
                "probability": probability
            })
        
        # Get model info
        with get_db_context() as db:
            active_model = db.query(MLModel).filter(MLModel.is_active == True).first()
        
        return {
            "predictions": predictions,
            "model_version": active_model.version,
            "model_type": active_model.model_type,
            "count": len(predictions)
        }
    
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feature-importance")
def get_feature_importance(version: Optional[str] = None, top_n: int = 20):
    """
    Get feature importance from a model.
    
    Args:
        version: Model version (uses active model if None)
        top_n: Number of top features to return
    """
    with get_db_context() as db:
        if version:
            model = db.query(MLModel).filter(MLModel.version == version).first()
        else:
            model = db.query(MLModel).filter(MLModel.is_active == True).first()
        
        if model is None:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Get feature importance
        importance = model.feature_importance or {}
        
        # Sort and limit
        sorted_importance = dict(
            sorted(importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
        )
        
        return {
            "version": model.version,
            "model_type": model.model_type,
            "feature_importance": sorted_importance,
            "top_n": top_n
        }


@router.delete("/models/{version}")
def delete_model(version: str):
    """
    Delete a model.
    
    Args:
        version: Model version to delete
    """
    with get_db_context() as db:
        model = db.query(MLModel).filter(MLModel.version == version).first()
        
        if model is None:
            raise HTTPException(status_code=404, detail=f"Model {version} not found")
        
        if model.is_active:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete active model. Activate another model first."
            )
        
        # Delete model file
        import os
        if os.path.exists(model.model_path):
            os.remove(model.model_path)
        
        # Delete from database
        db.delete(model)
        db.commit()
        
        logger.info(f"Deleted model: {version}")
        
        return {"message": f"Model {version} deleted"}

