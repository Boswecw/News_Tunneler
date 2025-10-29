"""
Advanced ML models for trading signal prediction.

Implements ensemble methods (Random Forest, XGBoost, Gradient Boosting)
with cross-validation, hyperparameter tuning, and model comparison.
"""
import os
import json
import logging
import pickle
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
)
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

logger = logging.getLogger(__name__)

# Feature columns (same as train_signals.py)
FEATURE_COLS = [
    "sentiment",
    "magnitude",
    "novelty",
    "credibility",
    "ret_1d",
    "vol_z",
    "vwap_dev",
    "gap_pct",
    "sector_momo_pct",
    "earnings_in_days",
]

# Model save directory
MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "models"
)


class AdvancedMLTrainer:
    """
    Advanced ML trainer with multiple model types and hyperparameter tuning.
    """
    
    def __init__(self, feature_cols: List[str] = None):
        """
        Initialize trainer.
        
        Args:
            feature_cols: List of feature column names
        """
        self.feature_cols = feature_cols or FEATURE_COLS
        self.scaler = StandardScaler()
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        
    def prepare_data(
        self,
        signals: List,
        test_size: float = 0.2
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare training and test data from signals.
        
        Args:
            signals: List of Signal objects with y_beat labels
            test_size: Fraction of data to use for testing
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        # Convert to DataFrame
        data = []
        for sig in signals:
            row = {"y_beat": sig.y_beat}
            for col in self.feature_cols:
                row[col] = sig.features.get(col, 0.0)
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Prepare features and labels
        X = df[self.feature_cols].fillna(0).values
        y = df["y_beat"].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42, stratify=y
        )
        
        return X_train, X_test, y_train, y_test
    
    def train_random_forest(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        tune_hyperparams: bool = False
    ) -> RandomForestClassifier:
        """
        Train Random Forest classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            tune_hyperparams: Whether to perform hyperparameter tuning
            
        Returns:
            Trained RandomForestClassifier
        """
        logger.info("Training Random Forest...")
        
        if tune_hyperparams:
            # Hyperparameter grid
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, 30, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
            }
            
            rf = RandomForestClassifier(random_state=42)
            grid_search = GridSearchCV(
                rf, param_grid, cv=5, scoring='roc_auc', n_jobs=-1, verbose=1
            )
            grid_search.fit(X_train, y_train)
            
            logger.info(f"Best RF params: {grid_search.best_params_}")
            model = grid_search.best_estimator_
        else:
            # Default parameters
            model = RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train, y_train)
        
        self.models['random_forest'] = model
        return model
    
    def train_xgboost(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        tune_hyperparams: bool = False
    ) -> XGBClassifier:
        """
        Train XGBoost classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            tune_hyperparams: Whether to perform hyperparameter tuning
            
        Returns:
            Trained XGBClassifier
        """
        logger.info("Training XGBoost...")
        
        if tune_hyperparams:
            # Hyperparameter grid
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.3],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0],
            }
            
            xgb = XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss')
            grid_search = GridSearchCV(
                xgb, param_grid, cv=5, scoring='roc_auc', n_jobs=-1, verbose=1
            )
            grid_search.fit(X_train, y_train)
            
            logger.info(f"Best XGB params: {grid_search.best_params_}")
            model = grid_search.best_estimator_
        else:
            # Default parameters
            model = XGBClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            model.fit(X_train, y_train)
        
        self.models['xgboost'] = model
        return model
    
    def train_lightgbm(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        tune_hyperparams: bool = False
    ) -> LGBMClassifier:
        """
        Train LightGBM classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            tune_hyperparams: Whether to perform hyperparameter tuning
            
        Returns:
            Trained LGBMClassifier
        """
        logger.info("Training LightGBM...")
        
        if tune_hyperparams:
            # Hyperparameter grid
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.3],
                'num_leaves': [31, 63, 127],
            }
            
            lgbm = LGBMClassifier(random_state=42, verbose=-1)
            grid_search = GridSearchCV(
                lgbm, param_grid, cv=5, scoring='roc_auc', n_jobs=-1, verbose=1
            )
            grid_search.fit(X_train, y_train)
            
            logger.info(f"Best LGBM params: {grid_search.best_params_}")
            model = grid_search.best_estimator_
        else:
            # Default parameters
            model = LGBMClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                num_leaves=31,
                random_state=42,
                verbose=-1
            )
            model.fit(X_train, y_train)
        
        self.models['lightgbm'] = model
        return model
    
    def train_gradient_boosting(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        tune_hyperparams: bool = False
    ) -> GradientBoostingClassifier:
        """
        Train Gradient Boosting classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            tune_hyperparams: Whether to perform hyperparameter tuning
            
        Returns:
            Trained GradientBoostingClassifier
        """
        logger.info("Training Gradient Boosting...")
        
        if tune_hyperparams:
            # Hyperparameter grid
            param_grid = {
                'n_estimators': [100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1],
                'subsample': [0.8, 1.0],
            }
            
            gb = GradientBoostingClassifier(random_state=42)
            grid_search = GridSearchCV(
                gb, param_grid, cv=5, scoring='roc_auc', n_jobs=-1, verbose=1
            )
            grid_search.fit(X_train, y_train)
            
            logger.info(f"Best GB params: {grid_search.best_params_}")
            model = grid_search.best_estimator_
        else:
            # Default parameters
            model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
            model.fit(X_train, y_train)
        
        self.models['gradient_boosting'] = model
        return model

    def evaluate_model(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_name: str
    ) -> Dict:
        """
        Evaluate model performance.

        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            model_name: Name of the model

        Returns:
            Dict with evaluation metrics
        """
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            'model_name': model_name,
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, zero_division=0)),
            'f1': float(f1_score(y_test, y_pred, zero_division=0)),
            'roc_auc': float(roc_auc_score(y_test, y_pred_proba)),
        }

        logger.info(f"{model_name} metrics: {metrics}")
        return metrics

    def compare_models(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """
        Compare all trained models and select the best one.

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Dict with comparison results
        """
        results = []

        for model_name, model in self.models.items():
            metrics = self.evaluate_model(model, X_test, y_test, model_name)
            results.append(metrics)

        # Sort by ROC AUC (best metric for imbalanced classification)
        results.sort(key=lambda x: x['roc_auc'], reverse=True)

        # Select best model
        best_result = results[0]
        self.best_model_name = best_result['model_name']
        self.best_model = self.models[self.best_model_name]

        logger.info(f"Best model: {self.best_model_name} (ROC AUC: {best_result['roc_auc']:.4f})")

        return {
            'best_model': self.best_model_name,
            'all_results': results,
        }

    def get_feature_importance(self, model_name: str = None) -> Dict[str, float]:
        """
        Get feature importance from a model.

        Args:
            model_name: Name of the model (uses best model if None)

        Returns:
            Dict mapping feature names to importance scores
        """
        if model_name is None:
            model_name = self.best_model_name
            model = self.best_model
        else:
            model = self.models.get(model_name)

        if model is None:
            raise ValueError(f"Model {model_name} not found")

        # Get feature importance
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        else:
            # For models without feature_importances_ (e.g., LogisticRegression)
            importances = np.abs(model.coef_[0])

        # Create dict mapping feature names to importance
        feature_importance = {
            col: float(imp)
            for col, imp in zip(self.feature_cols, importances)
        }

        # Sort by importance
        feature_importance = dict(
            sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        )

        return feature_importance

    def save_model(
        self,
        version: str,
        model_name: str = None,
        metrics: Dict = None
    ) -> str:
        """
        Save model to disk.

        Args:
            version: Model version string
            model_name: Name of the model to save (uses best model if None)
            metrics: Training metrics to save

        Returns:
            Path to saved model file
        """
        if model_name is None:
            model_name = self.best_model_name
            model = self.best_model
        else:
            model = self.models.get(model_name)

        if model is None:
            raise ValueError(f"Model {model_name} not found")

        # Create model directory
        os.makedirs(MODEL_DIR, exist_ok=True)

        # Save model
        model_filename = f"{model_name}_{version}.pkl"
        model_path = os.path.join(MODEL_DIR, model_filename)

        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': model,
                'scaler': self.scaler,
                'feature_cols': self.feature_cols,
                'model_name': model_name,
                'version': version,
                'metrics': metrics or {},
            }, f)

        logger.info(f"Saved model to {model_path}")
        return model_path

    def load_model(self, model_path: str):
        """
        Load model from disk.

        Args:
            model_path: Path to model file
        """
        with open(model_path, 'rb') as f:
            data = pickle.load(f)

        self.best_model = data['model']
        self.scaler = data['scaler']
        self.feature_cols = data['feature_cols']
        self.best_model_name = data['model_name']

        logger.info(f"Loaded model from {model_path}")

    def predict(self, features: Dict) -> Tuple[int, float]:
        """
        Make prediction using the best model.

        Args:
            features: Dict of feature values

        Returns:
            Tuple of (prediction, probability)
        """
        if self.best_model is None:
            raise ValueError("No model loaded")

        # Prepare features
        X = np.array([[features.get(col, 0.0) for col in self.feature_cols]])
        X_scaled = self.scaler.transform(X)

        # Make prediction
        prediction = int(self.best_model.predict(X_scaled)[0])
        probability = float(self.best_model.predict_proba(X_scaled)[0][1])

        return prediction, probability

