"""
ML training pipeline for trading signals.

Integrates data collection, feature engineering, model training,
evaluation, and deployment.
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from app.core.db import get_db_context
from app.models.signal import Signal
from app.models.ml_model import MLModel
from app.ml.advanced_models import AdvancedMLTrainer
from app.ml.feature_engineering import FeatureEngineer
from app.ml.explainability import ModelExplainer

logger = logging.getLogger(__name__)


class MLTrainingPipeline:
    """
    End-to-end ML training pipeline.
    """
    
    def __init__(
        self,
        use_feature_engineering: bool = True,
        tune_hyperparams: bool = False
    ):
        """
        Initialize training pipeline.
        
        Args:
            use_feature_engineering: Whether to use advanced feature engineering
            tune_hyperparams: Whether to perform hyperparameter tuning
        """
        self.use_feature_engineering = use_feature_engineering
        self.tune_hyperparams = tune_hyperparams
        self.feature_engineer = FeatureEngineer() if use_feature_engineering else None
        self.trainer = None
        self.explainer = None
        
    def collect_training_data(
        self,
        min_samples: int = 50,
        include_features: bool = True
    ) -> List[Signal]:
        """
        Collect labeled signals from database.
        
        Args:
            min_samples: Minimum number of labeled samples required
            include_features: Whether to include feature engineering
            
        Returns:
            List of Signal objects with labels
        """
        logger.info("Collecting training data from database")
        
        with get_db_context() as db:
            # Load labeled signals
            labeled = db.query(Signal).filter(Signal.y_beat.isnot(None)).all()
            
            if len(labeled) < min_samples:
                raise ValueError(
                    f"Insufficient training data: {len(labeled)} < {min_samples}"
                )
            
            logger.info(f"Collected {len(labeled)} labeled signals")
            
            # Optionally add engineered features
            if include_features and self.feature_engineer:
                logger.info("Adding engineered features")
                for signal in labeled:
                    try:
                        # Engineer features
                        timestamp = datetime.fromtimestamp(signal.t / 1000)
                        engineered = self.feature_engineer.engineer_all_features(
                            signal.features,
                            signal.symbol,
                            timestamp
                        )
                        # Update signal features
                        signal.features = engineered
                    except Exception as e:
                        logger.warning(f"Failed to engineer features for {signal.symbol}: {e}")
            
            return labeled
    
    def train_all_models(
        self,
        signals: List[Signal],
        model_types: List[str] = None
    ) -> Dict:
        """
        Train all model types and compare performance.
        
        Args:
            signals: List of labeled signals
            model_types: List of model types to train (trains all if None)
            
        Returns:
            Dict with training results
        """
        if model_types is None:
            model_types = ['random_forest', 'xgboost', 'lightgbm', 'gradient_boosting']
        
        logger.info(f"Training {len(model_types)} model types")
        
        # Initialize trainer
        self.trainer = AdvancedMLTrainer()
        
        # Prepare data
        X_train, X_test, y_train, y_test = self.trainer.prepare_data(signals)
        
        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        logger.info(f"Class balance: {y_train.mean():.3f}")
        
        # Train each model type
        for model_type in model_types:
            try:
                if model_type == 'random_forest':
                    self.trainer.train_random_forest(
                        X_train, y_train, tune_hyperparams=self.tune_hyperparams
                    )
                elif model_type == 'xgboost':
                    self.trainer.train_xgboost(
                        X_train, y_train, tune_hyperparams=self.tune_hyperparams
                    )
                elif model_type == 'lightgbm':
                    self.trainer.train_lightgbm(
                        X_train, y_train, tune_hyperparams=self.tune_hyperparams
                    )
                elif model_type == 'gradient_boosting':
                    self.trainer.train_gradient_boosting(
                        X_train, y_train, tune_hyperparams=self.tune_hyperparams
                    )
                else:
                    logger.warning(f"Unknown model type: {model_type}")
            
            except Exception as e:
                logger.error(f"Error training {model_type}: {e}", exc_info=True)
        
        # Compare models
        comparison = self.trainer.compare_models(X_test, y_test)
        
        logger.info(f"Best model: {comparison['best_model']}")
        
        return {
            'comparison': comparison,
            'n_train': len(X_train),
            'n_test': len(X_test),
            'class_balance': float(y_train.mean()),
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
        }
    
    def create_explainer(self, X_train) -> ModelExplainer:
        """
        Create model explainer with SHAP values.
        
        Args:
            X_train: Training data
            
        Returns:
            ModelExplainer instance
        """
        if self.trainer is None:
            raise ValueError("No trained models available")
        
        logger.info("Creating model explainer")
        
        self.explainer = ModelExplainer(self.trainer)
        self.explainer.create_explainer(X_train)
        
        return self.explainer
    
    def save_model_to_db(
        self,
        version: str,
        metrics: Dict,
        training_samples: int,
        set_active: bool = True
    ) -> MLModel:
        """
        Save trained model to database.
        
        Args:
            version: Model version string
            metrics: Training metrics
            training_samples: Number of training samples
            set_active: Whether to set this model as active
            
        Returns:
            MLModel instance
        """
        if self.trainer is None or self.trainer.best_model is None:
            raise ValueError("No trained model available")
        
        logger.info(f"Saving model to database: {version}")
        
        # Save model to disk
        model_path = self.trainer.save_model(version, metrics=metrics)
        
        # Get feature importance
        feature_importance = self.trainer.get_feature_importance()
        
        # Get hyperparameters
        best_model = self.trainer.best_model
        hyperparameters = {}
        if hasattr(best_model, 'get_params'):
            hyperparameters = {
                k: str(v) for k, v in best_model.get_params().items()
                if not k.startswith('_')
            }
        
        with get_db_context() as db:
            # Deactivate all models if setting this one as active
            if set_active:
                db.query(MLModel).update({'is_active': False})
            
            # Check if version exists
            existing = db.query(MLModel).filter(MLModel.version == version).first()
            
            if existing:
                # Update existing
                existing.model_type = self.trainer.best_model_name
                existing.model_path = model_path
                existing.metrics = metrics
                existing.feature_importance = feature_importance
                existing.hyperparameters = hyperparameters
                existing.training_samples = training_samples
                existing.is_active = set_active
                db.add(existing)
                ml_model = existing
            else:
                # Create new
                ml_model = MLModel(
                    version=version,
                    model_type=self.trainer.best_model_name,
                    model_path=model_path,
                    metrics=metrics,
                    feature_importance=feature_importance,
                    hyperparameters=hyperparameters,
                    training_samples=training_samples,
                    is_active=set_active
                )
                db.add(ml_model)
            
            db.commit()
            db.refresh(ml_model)
            
            logger.info(f"Saved model to database: {ml_model.id}")
            
            return ml_model
    
    def run_full_pipeline(
        self,
        min_samples: int = 50,
        model_types: List[str] = None,
        version: str = None
    ) -> Dict:
        """
        Run the full training pipeline.
        
        Args:
            min_samples: Minimum number of labeled samples
            model_types: List of model types to train
            version: Model version (auto-generated if None)
            
        Returns:
            Dict with pipeline results
        """
        logger.info("Starting full ML training pipeline")
        
        # Generate version if not provided
        if version is None:
            version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Step 1: Collect training data
        signals = self.collect_training_data(min_samples=min_samples)
        
        # Step 2: Train all models
        training_results = self.train_all_models(signals, model_types=model_types)
        
        # Step 3: Create explainer
        explainer = self.create_explainer(training_results['X_train'])
        
        # Calculate SHAP values for test set
        shap_values = explainer.explain_predictions(training_results['X_test'])
        
        # Get feature importance from SHAP
        shap_importance = explainer.get_feature_importance(shap_values, top_n=10)
        
        # Step 4: Save model to database
        best_result = training_results['comparison']['all_results'][0]
        ml_model = self.save_model_to_db(
            version=version,
            metrics=best_result,
            training_samples=training_results['n_train']
        )
        
        logger.info("ML training pipeline completed successfully")
        
        return {
            'version': version,
            'model_id': ml_model.id,
            'model_type': ml_model.model_type,
            'metrics': best_result,
            'feature_importance': shap_importance,
            'training_samples': training_results['n_train'],
            'test_samples': training_results['n_test'],
            'class_balance': training_results['class_balance'],
        }

