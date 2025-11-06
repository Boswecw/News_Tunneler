"""
Celery tasks for ML operations.

Provides async tasks for:
- Model training
- Batch predictions
- Sentiment updates with FinBERT
- Scheduled model retraining
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from celery import Task
from app.core.celery_app import celery_app
from app.core.db import get_db_context
from app.models.signal import Signal
from app.models.ml_model import MLModel
from app.ml.training_pipeline import MLTrainingPipeline
from app.ml.advanced_models import AdvancedMLTrainer
from app.core.sentiment_advanced import batch_analyze_sentiment, analyze_combined_sentiment

logger = logging.getLogger(__name__)


class MLTask(Task):
    """Base task for ML operations with error handling."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


@celery_app.task(base=MLTask, name="ml.train_model", queue="llm")
def train_ml_model_task(
    min_samples: int = 50,
    model_types: Optional[List[str]] = None,
    tune_hyperparams: bool = False,
    use_feature_engineering: bool = True
) -> Dict:
    """
    Train ML models asynchronously.
    
    Args:
        min_samples: Minimum number of labeled samples required
        model_types: List of model types to train (None = all)
        tune_hyperparams: Whether to tune hyperparameters
        use_feature_engineering: Whether to use feature engineering
        
    Returns:
        Dict with training results
    """
    logger.info(f"Starting ML training task: min_samples={min_samples}, models={model_types}")
    
    try:
        # Create pipeline
        pipeline = MLTrainingPipeline(
            use_feature_engineering=use_feature_engineering,
            tune_hyperparams=tune_hyperparams
        )
        
        # Run training
        results = pipeline.run_full_pipeline(
            min_samples=min_samples,
            model_types=model_types
        )
        
        logger.info(f"Training completed: {results['version']}")
        
        return {
            'status': 'success',
            'version': results['version'],
            'model_id': results['model_id'],
            'model_type': results['model_type'],
            'metrics': results['metrics'],
            'training_samples': results['training_samples'],
            'test_samples': results['test_samples'],
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(base=MLTask, name="ml.batch_predict", queue="llm")
def batch_predict_task(signal_ids: List[int], model_version: Optional[str] = None) -> Dict:
    """
    Make batch predictions for signals.
    
    Args:
        signal_ids: List of signal IDs to predict
        model_version: Model version to use (None = active model)
        
    Returns:
        Dict with prediction results
    """
    logger.info(f"Starting batch prediction: {len(signal_ids)} signals")
    
    try:
        with get_db_context() as db:
            # Get model
            if model_version:
                model = db.query(MLModel).filter(MLModel.version == model_version).first()
            else:
                model = db.query(MLModel).filter(MLModel.is_active == True).first()
            
            if not model:
                raise ValueError(f"Model not found: {model_version or 'active'}")
            
            # Load model
            trainer = AdvancedMLTrainer()
            trainer.load_model(model.model_path)
            
            # Get signals
            signals = db.query(Signal).filter(Signal.id.in_(signal_ids)).all()
            
            # Make predictions
            predictions = []
            for signal in signals:
                features = signal.features or {}
                prediction, probability = trainer.predict(features)
                
                predictions.append({
                    'signal_id': signal.id,
                    'prediction': prediction,
                    'probability': probability
                })
            
            logger.info(f"Batch prediction completed: {len(predictions)} predictions")
            
            return {
                'status': 'success',
                'model_version': model.version,
                'predictions': predictions,
                'count': len(predictions),
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
    
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(base=MLTask, name="ml.update_sentiment", queue="llm")
def update_sentiment_task(signal_ids: Optional[List[int]] = None, days_back: int = 7) -> Dict:
    """
    Update sentiment for signals using FinBERT.
    
    Args:
        signal_ids: List of signal IDs to update (None = recent signals)
        days_back: Number of days back to update (if signal_ids is None)
        
    Returns:
        Dict with update results
    """
    logger.info(f"Starting sentiment update: signal_ids={signal_ids}, days_back={days_back}")
    
    try:
        with get_db_context() as db:
            # Get signals
            if signal_ids:
                signals = db.query(Signal).filter(Signal.id.in_(signal_ids)).all()
            else:
                cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
                signals = db.query(Signal).filter(Signal.created_at >= cutoff).all()
            
            # Collect texts
            texts = []
            signal_map = {}
            for signal in signals:
                # Get text from features or label
                text = signal.label or ""
                if text:
                    texts.append(text)
                    signal_map[len(texts) - 1] = signal
            
            if not texts:
                logger.warning("No texts found for sentiment update")
                return {
                    'status': 'success',
                    'updated': 0,
                    'message': 'No texts to update'
                }
            
            # Batch analyze sentiment
            logger.info(f"Analyzing sentiment for {len(texts)} texts")
            results = batch_analyze_sentiment(texts)
            
            # Update signals
            updated = 0
            for i, result in enumerate(results):
                signal = signal_map.get(i)
                if signal and signal.features:
                    # Update sentiment in features
                    signal.features['sentiment'] = result['sentiment']
                    signal.features['sentiment_confidence'] = result['confidence']
                    signal.features['sentiment_model'] = result['model']
                    db.add(signal)
                    updated += 1
            
            db.commit()
            
            logger.info(f"Sentiment update completed: {updated} signals updated")
            
            return {
                'status': 'success',
                'updated': updated,
                'total': len(signals),
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
    
    except Exception as e:
        logger.error(f"Sentiment update failed: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(base=MLTask, name="ml.scheduled_retrain", queue="llm")
def scheduled_retrain_task(min_samples: int = 100, min_new_samples: int = 20) -> Dict:
    """
    Scheduled task to retrain models with new data.
    
    Runs daily to check if there's enough new labeled data to retrain.
    
    Args:
        min_samples: Minimum total samples required
        min_new_samples: Minimum new samples since last training
        
    Returns:
        Dict with retraining results
    """
    logger.info(f"Starting scheduled retrain check: min_samples={min_samples}, min_new_samples={min_new_samples}")
    
    try:
        with get_db_context() as db:
            # Get total labeled signals
            total_signals = db.query(Signal).filter(Signal.y_beat.isnot(None)).count()
            
            if total_signals < min_samples:
                logger.info(f"Not enough samples for retraining: {total_signals} < {min_samples}")
                return {
                    'status': 'skipped',
                    'reason': 'insufficient_samples',
                    'total_signals': total_signals,
                    'min_samples': min_samples
                }
            
            # Get last training time
            last_model = db.query(MLModel).order_by(MLModel.created_at.desc()).first()
            
            if last_model:
                # Count new signals since last training
                new_signals = db.query(Signal).filter(
                    Signal.y_beat.isnot(None),
                    Signal.created_at > last_model.created_at
                ).count()
                
                if new_signals < min_new_samples:
                    logger.info(f"Not enough new samples: {new_signals} < {min_new_samples}")
                    return {
                        'status': 'skipped',
                        'reason': 'insufficient_new_samples',
                        'new_signals': new_signals,
                        'min_new_samples': min_new_samples,
                        'last_training': last_model.created_at.isoformat()
                    }
            
            # Trigger training
            logger.info(f"Triggering retraining: {total_signals} total samples")
            result = train_ml_model_task.delay(
                min_samples=min_samples,
                model_types=['random_forest', 'xgboost', 'lightgbm'],
                tune_hyperparams=True,
                use_feature_engineering=True
            )
            
            return {
                'status': 'triggered',
                'task_id': result.id,
                'total_signals': total_signals,
                'new_signals': new_signals if last_model else total_signals,
                'triggered_at': datetime.now(timezone.utc).isoformat()
            }
    
    except Exception as e:
        logger.error(f"Scheduled retrain failed: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(base=MLTask, name="ml.evaluate_model", queue="llm")
def evaluate_model_task(model_version: str, signal_ids: Optional[List[int]] = None) -> Dict:
    """
    Evaluate a model on a set of signals.
    
    Args:
        model_version: Model version to evaluate
        signal_ids: List of signal IDs to evaluate on (None = all labeled signals)
        
    Returns:
        Dict with evaluation results
    """
    logger.info(f"Starting model evaluation: {model_version}")
    
    try:
        with get_db_context() as db:
            # Get model
            model = db.query(MLModel).filter(MLModel.version == model_version).first()
            if not model:
                raise ValueError(f"Model not found: {model_version}")
            
            # Load model
            trainer = AdvancedMLTrainer()
            trainer.load_model(model.model_path)
            
            # Get signals
            query = db.query(Signal).filter(Signal.y_beat.isnot(None))
            if signal_ids:
                query = query.filter(Signal.id.in_(signal_ids))
            
            signals = query.all()
            
            if len(signals) < 10:
                raise ValueError(f"Not enough signals for evaluation: {len(signals)}")
            
            # Prepare data
            X_test, _, y_test, _ = trainer.prepare_data(signals, test_size=1.0)
            
            # Evaluate
            metrics = trainer.evaluate_model(trainer.best_model, X_test, y_test)
            
            logger.info(f"Evaluation completed: {metrics}")
            
            return {
                'status': 'success',
                'model_version': model_version,
                'metrics': metrics,
                'num_samples': len(signals),
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
    
    except Exception as e:
        logger.error(f"Model evaluation failed: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now(timezone.utc).isoformat()
        }

