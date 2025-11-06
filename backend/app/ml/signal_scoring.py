"""
ML-enhanced signal scoring.

Integrates ML predictions into signal generation and scoring.
"""
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
from app.core.db import get_db_context
from app.models.ml_model import MLModel
from app.ml.advanced_models import AdvancedMLTrainer
from app.ml.feature_store import FeatureStore
from app.core.feature_flags import FeatureFlagManager, FeatureFlag

logger = logging.getLogger(__name__)

# Global instances
_active_trainer: Optional[AdvancedMLTrainer] = None
_feature_store: Optional[FeatureStore] = None
_feature_flags = FeatureFlagManager()


def get_active_trainer() -> Optional[AdvancedMLTrainer]:
    """
    Get or load the active ML model.
    
    Returns:
        AdvancedMLTrainer instance or None if no active model
    """
    global _active_trainer
    
    # Check if ML predictions are enabled
    if not _feature_flags.is_enabled(FeatureFlag.ML_PREDICTIONS):
        return None
    
    if _active_trainer is None:
        try:
            # Load active model from database
            with get_db_context() as db:
                active_model = db.query(MLModel).filter(MLModel.is_active == True).first()
                
                if active_model is None:
                    logger.warning("No active ML model found")
                    return None
                
                # Load model
                _active_trainer = AdvancedMLTrainer()
                _active_trainer.load_model(active_model.model_path)
                
                logger.info(f"Loaded active ML model: {active_model.version}")
        
        except Exception as e:
            logger.error(f"Failed to load active model: {e}", exc_info=True)
            return None
    
    return _active_trainer


def get_feature_store() -> FeatureStore:
    """
    Get or create feature store.
    
    Returns:
        FeatureStore instance
    """
    global _feature_store
    
    if _feature_store is None:
        _feature_store = FeatureStore(ttl=3600, version="v1")
    
    return _feature_store


def enhance_features_with_ml(
    symbol: str,
    base_features: Dict[str, float],
    use_feature_engineering: bool = True
) -> Dict[str, float]:
    """
    Enhance base features with ML-engineered features.
    
    Args:
        symbol: Stock symbol
        base_features: Base features dict
        use_feature_engineering: Whether to add engineered features
        
    Returns:
        Enhanced features dict
    """
    enhanced = base_features.copy()
    
    if not use_feature_engineering:
        return enhanced

    if not _feature_flags.is_enabled(FeatureFlag.ADVANCED_ML):
        return enhanced
    
    try:
        feature_store = get_feature_store()
        
        # Get sentiment values from base features
        sentiment = base_features.get('sentiment', 0.0)
        magnitude = base_features.get('magnitude', 3.0)
        credibility = base_features.get('credibility', 3.0)

        # Get all engineered features
        engineered = feature_store.get_all_features(
            symbol=symbol,
            sentiment=sentiment,
            magnitude=magnitude,
            credibility=credibility,
            base_features=base_features,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Merge engineered features
        enhanced.update(engineered)
        
        logger.debug(f"Enhanced features for {symbol}: {len(enhanced)} total features")
    
    except Exception as e:
        logger.error(f"Failed to enhance features: {e}", exc_info=True)
    
    return enhanced


def get_ml_prediction(features: Dict[str, float]) -> Optional[Tuple[int, float]]:
    """
    Get ML prediction for features.
    
    Args:
        features: Feature dict
        
    Returns:
        Tuple of (prediction, probability) or None if ML disabled
    """
    trainer = get_active_trainer()
    
    if trainer is None:
        return None
    
    try:
        prediction, probability = trainer.predict(features)
        return prediction, probability
    
    except Exception as e:
        logger.error(f"ML prediction failed: {e}", exc_info=True)
        return None


def calculate_ml_enhanced_score(
    base_score: float,
    base_label: str,
    features: Dict[str, float],
    ml_weight: float = 0.3
) -> Dict:
    """
    Calculate ML-enhanced score.
    
    Combines traditional scoring with ML predictions.
    
    Args:
        base_score: Base score from traditional scoring (0-100)
        base_label: Base label (High-Conviction, Opportunity, Watch, Ignore)
        features: Feature dict
        ml_weight: Weight for ML prediction (0-1)
        
    Returns:
        Dict with enhanced score, label, and ML metadata
    """
    # Get ML prediction
    ml_result = get_ml_prediction(features)
    
    if ml_result is None:
        # ML disabled or failed, return base score
        return {
            'score': base_score,
            'label': base_label,
            'ml_enabled': False,
            'ml_prediction': None,
            'ml_probability': None,
            'ml_boost': 0.0
        }
    
    prediction, probability = ml_result
    
    # Calculate ML boost
    # If ML predicts success (1), boost score based on confidence
    # If ML predicts failure (0), reduce score based on confidence
    if prediction == 1:
        # Positive prediction: boost score
        ml_boost = (probability - 0.5) * 2 * 20  # Max boost: +20 points
    else:
        # Negative prediction: reduce score
        ml_boost = -(probability - 0.5) * 2 * 20  # Max reduction: -20 points
    
    # Apply ML weight
    weighted_boost = ml_boost * ml_weight
    
    # Calculate final score
    final_score = base_score + weighted_boost
    final_score = max(0, min(100, final_score))  # Clamp to 0-100
    
    # Determine final label
    if final_score >= 75:
        final_label = "High-Conviction"
    elif final_score >= 60:
        final_label = "Opportunity"
    elif final_score >= 45:
        final_label = "Watch"
    else:
        final_label = "Ignore"
    
    return {
        'score': round(final_score, 1),
        'label': final_label,
        'ml_enabled': True,
        'ml_prediction': prediction,
        'ml_probability': round(probability, 3),
        'ml_boost': round(weighted_boost, 2),
        'base_score': base_score,
        'base_label': base_label
    }


def score_signal_with_ml(
    symbol: str,
    base_features: Dict[str, float],
    base_score: float,
    base_label: str,
    use_feature_engineering: bool = True,
    ml_weight: float = 0.3
) -> Dict:
    """
    Score signal with ML enhancement.
    
    This is the main entry point for ML-enhanced signal scoring.
    
    Args:
        symbol: Stock symbol
        base_features: Base features from traditional scoring
        base_score: Base score (0-100)
        base_label: Base label
        use_feature_engineering: Whether to use feature engineering
        ml_weight: Weight for ML prediction (0-1)
        
    Returns:
        Dict with enhanced score and metadata
    """
    # Enhance features
    enhanced_features = enhance_features_with_ml(
        symbol=symbol,
        base_features=base_features,
        use_feature_engineering=use_feature_engineering
    )
    
    # Calculate ML-enhanced score
    result = calculate_ml_enhanced_score(
        base_score=base_score,
        base_label=base_label,
        features=enhanced_features,
        ml_weight=ml_weight
    )
    
    # Add enhanced features to result
    result['features'] = enhanced_features
    result['num_features'] = len(enhanced_features)
    result['num_base_features'] = len(base_features)
    result['num_engineered_features'] = len(enhanced_features) - len(base_features)
    
    return result


def invalidate_ml_cache():
    """Invalidate ML model and feature cache."""
    global _active_trainer, _feature_store
    
    _active_trainer = None
    
    if _feature_store:
        _feature_store.invalidate_all()
    
    logger.info("ML cache invalidated")


def get_ml_status() -> Dict:
    """
    Get ML system status.
    
    Returns:
        Dict with ML system status
    """
    trainer = get_active_trainer()
    feature_store = get_feature_store()
    
    status = {
        'ml_predictions_enabled': _feature_flags.is_enabled(FeatureFlag.ML_PREDICTIONS),
        'feature_engineering_enabled': _feature_flags.is_enabled(FeatureFlag.ADVANCED_ML),
        'active_model_loaded': trainer is not None,
        'feature_store_stats': feature_store.get_cache_stats() if feature_store else None
    }
    
    if trainer:
        with get_db_context() as db:
            active_model = db.query(MLModel).filter(MLModel.is_active == True).first()
            if active_model:
                status['active_model'] = {
                    'version': active_model.version,
                    'model_type': active_model.model_type,
                    'metrics': active_model.metrics,
                    'training_samples': active_model.training_samples,
                    'created_at': active_model.created_at.isoformat()
                }
    
    return status

