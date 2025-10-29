"""
Model explainability using SHAP (SHapley Additive exPlanations).

Provides feature importance, feature contributions, and model interpretation
for trading signal predictions.
"""
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import shap
from app.ml.advanced_models import AdvancedMLTrainer

logger = logging.getLogger(__name__)


class ModelExplainer:
    """
    Model explainability using SHAP values.
    """
    
    def __init__(self, trainer: AdvancedMLTrainer):
        """
        Initialize explainer.
        
        Args:
            trainer: Trained AdvancedMLTrainer instance
        """
        self.trainer = trainer
        self.explainer = None
        self.shap_values = None
        self.base_value = None
        
    def create_explainer(
        self,
        X_train: np.ndarray,
        model_name: str = None,
        explainer_type: str = "auto"
    ):
        """
        Create SHAP explainer for a model.
        
        Args:
            X_train: Training data for background samples
            model_name: Name of model to explain (uses best model if None)
            explainer_type: Type of explainer ('tree', 'kernel', 'linear', 'auto')
        """
        if model_name is None:
            model_name = self.trainer.best_model_name
            model = self.trainer.best_model
        else:
            model = self.trainer.models.get(model_name)
        
        if model is None:
            raise ValueError(f"Model {model_name} not found")
        
        logger.info(f"Creating SHAP explainer for {model_name}")
        
        # Select appropriate explainer based on model type
        if explainer_type == "auto":
            if model_name in ['random_forest', 'xgboost', 'lightgbm', 'gradient_boosting']:
                explainer_type = "tree"
            else:
                explainer_type = "kernel"
        
        # Create explainer
        if explainer_type == "tree":
            # TreeExplainer for tree-based models (fast)
            self.explainer = shap.TreeExplainer(model)
        elif explainer_type == "kernel":
            # KernelExplainer for any model (slower but universal)
            # Use a subset of training data as background
            background = shap.sample(X_train, min(100, len(X_train)))
            self.explainer = shap.KernelExplainer(model.predict_proba, background)
        elif explainer_type == "linear":
            # LinearExplainer for linear models
            self.explainer = shap.LinearExplainer(model, X_train)
        else:
            raise ValueError(f"Unknown explainer type: {explainer_type}")
        
        logger.info(f"Created {explainer_type} explainer")
    
    def explain_predictions(
        self,
        X: np.ndarray,
        check_additivity: bool = False
    ) -> np.ndarray:
        """
        Calculate SHAP values for predictions.
        
        Args:
            X: Features to explain
            check_additivity: Whether to check SHAP value additivity
            
        Returns:
            SHAP values array
        """
        if self.explainer is None:
            raise ValueError("Explainer not created. Call create_explainer() first.")
        
        logger.info(f"Calculating SHAP values for {len(X)} samples")
        
        # Calculate SHAP values
        shap_values = self.explainer.shap_values(X, check_additivity=check_additivity)
        
        # For binary classification, shap_values might be a list
        if isinstance(shap_values, list):
            # Use SHAP values for positive class (index 1)
            shap_values = shap_values[1]
        
        self.shap_values = shap_values
        
        # Get base value (expected value)
        if hasattr(self.explainer, 'expected_value'):
            expected_value = self.explainer.expected_value
            if isinstance(expected_value, (list, np.ndarray)):
                self.base_value = expected_value[1] if len(expected_value) > 1 else expected_value[0]
            else:
                self.base_value = expected_value
        else:
            self.base_value = 0.0
        
        return shap_values
    
    def get_feature_importance(
        self,
        shap_values: np.ndarray = None,
        top_n: int = None
    ) -> Dict[str, float]:
        """
        Get global feature importance from SHAP values.
        
        Args:
            shap_values: SHAP values (uses stored values if None)
            top_n: Return only top N features (returns all if None)
            
        Returns:
            Dict mapping feature names to importance scores
        """
        if shap_values is None:
            shap_values = self.shap_values
        
        if shap_values is None:
            raise ValueError("No SHAP values available")
        
        # Calculate mean absolute SHAP value for each feature
        importance = np.abs(shap_values).mean(axis=0)
        
        # Create dict mapping feature names to importance
        feature_importance = {
            col: float(imp)
            for col, imp in zip(self.trainer.feature_cols, importance)
        }
        
        # Sort by importance
        feature_importance = dict(
            sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        )
        
        # Return top N if specified
        if top_n is not None:
            feature_importance = dict(list(feature_importance.items())[:top_n])
        
        return feature_importance
    
    def explain_single_prediction(
        self,
        features: Dict,
        top_n: int = 10
    ) -> Dict:
        """
        Explain a single prediction with feature contributions.
        
        Args:
            features: Dict of feature values
            top_n: Number of top contributing features to return
            
        Returns:
            Dict with prediction, base value, and feature contributions
        """
        if self.explainer is None:
            raise ValueError("Explainer not created. Call create_explainer() first.")
        
        # Prepare features
        X = np.array([[features.get(col, 0.0) for col in self.trainer.feature_cols]])
        X_scaled = self.trainer.scaler.transform(X)
        
        # Get prediction
        prediction = int(self.trainer.best_model.predict(X_scaled)[0])
        probability = float(self.trainer.best_model.predict_proba(X_scaled)[0][1])
        
        # Calculate SHAP values
        shap_values = self.explainer.shap_values(X_scaled)
        
        # Handle list output for binary classification
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        # Get base value
        if hasattr(self.explainer, 'expected_value'):
            expected_value = self.explainer.expected_value
            if isinstance(expected_value, (list, np.ndarray)):
                base_value = expected_value[1] if len(expected_value) > 1 else expected_value[0]
            else:
                base_value = expected_value
        else:
            base_value = 0.5
        
        # Create feature contributions
        contributions = []
        for i, col in enumerate(self.trainer.feature_cols):
            contributions.append({
                'feature': col,
                'value': float(features.get(col, 0.0)),
                'contribution': float(shap_values[0][i]),
                'abs_contribution': float(abs(shap_values[0][i]))
            })
        
        # Sort by absolute contribution
        contributions.sort(key=lambda x: x['abs_contribution'], reverse=True)
        
        # Return top N
        top_contributions = contributions[:top_n]
        
        return {
            'prediction': prediction,
            'probability': probability,
            'base_value': float(base_value),
            'top_contributions': top_contributions,
            'all_contributions': contributions
        }
    
    def get_summary_plot_data(
        self,
        X: np.ndarray,
        shap_values: np.ndarray = None,
        max_display: int = 20
    ) -> Dict:
        """
        Get data for SHAP summary plot.
        
        Args:
            X: Feature values
            shap_values: SHAP values (uses stored values if None)
            max_display: Maximum number of features to display
            
        Returns:
            Dict with summary plot data
        """
        if shap_values is None:
            shap_values = self.shap_values
        
        if shap_values is None:
            raise ValueError("No SHAP values available")
        
        # Calculate feature importance
        importance = np.abs(shap_values).mean(axis=0)
        
        # Get top features
        top_indices = np.argsort(importance)[::-1][:max_display]
        
        # Create summary data
        summary_data = []
        for idx in top_indices:
            feature_name = self.trainer.feature_cols[idx]
            feature_values = X[:, idx]
            feature_shap = shap_values[:, idx]
            
            summary_data.append({
                'feature': feature_name,
                'importance': float(importance[idx]),
                'mean_shap': float(np.mean(feature_shap)),
                'mean_abs_shap': float(np.mean(np.abs(feature_shap))),
                'min_value': float(np.min(feature_values)),
                'max_value': float(np.max(feature_values)),
                'mean_value': float(np.mean(feature_values)),
            })
        
        return {
            'summary': summary_data,
            'base_value': float(self.base_value) if self.base_value is not None else 0.0
        }
    
    def get_dependence_plot_data(
        self,
        feature_name: str,
        X: np.ndarray,
        shap_values: np.ndarray = None
    ) -> Dict:
        """
        Get data for SHAP dependence plot for a specific feature.
        
        Args:
            feature_name: Name of feature to analyze
            X: Feature values
            shap_values: SHAP values (uses stored values if None)
            
        Returns:
            Dict with dependence plot data
        """
        if shap_values is None:
            shap_values = self.shap_values
        
        if shap_values is None:
            raise ValueError("No SHAP values available")
        
        # Get feature index
        if feature_name not in self.trainer.feature_cols:
            raise ValueError(f"Feature {feature_name} not found")
        
        feature_idx = self.trainer.feature_cols.index(feature_name)
        
        # Get feature values and SHAP values
        feature_values = X[:, feature_idx]
        feature_shap = shap_values[:, feature_idx]
        
        # Create data points
        data_points = [
            {
                'value': float(val),
                'shap': float(shap)
            }
            for val, shap in zip(feature_values, feature_shap)
        ]
        
        return {
            'feature': feature_name,
            'data_points': data_points,
            'correlation': float(np.corrcoef(feature_values, feature_shap)[0, 1])
        }

