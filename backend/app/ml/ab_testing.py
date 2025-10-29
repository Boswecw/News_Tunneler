"""
A/B Testing framework for ML models.

Allows comparing multiple model versions in production with traffic splitting.
"""
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from app.core.db import get_db_context
from app.models.signal import Signal
from app.models.ml_model import MLModel
from app.ml.advanced_models import AdvancedMLTrainer

logger = logging.getLogger(__name__)


class ABTest:
    """
    A/B test for comparing ML models.
    
    Features:
    - Traffic splitting by hash
    - Performance comparison
    - Statistical significance testing
    - Automatic winner selection
    """
    
    def __init__(
        self,
        model_a_version: str,
        model_b_version: str,
        traffic_split: float = 0.5,
        name: Optional[str] = None
    ):
        """
        Initialize A/B test.
        
        Args:
            model_a_version: Version of model A (control)
            model_b_version: Version of model B (treatment)
            traffic_split: Fraction of traffic to model B (0-1)
            name: Optional name for the test
        """
        self.model_a_version = model_a_version
        self.model_b_version = model_b_version
        self.traffic_split = traffic_split
        self.name = name or f"ab_test_{model_a_version}_vs_{model_b_version}"
        
        # Load models
        self.model_a = None
        self.model_b = None
        self.trainer_a = None
        self.trainer_b = None
        self._load_models()
    
    def _load_models(self):
        """Load both models from database."""
        with get_db_context() as db:
            self.model_a = db.query(MLModel).filter(
                MLModel.version == self.model_a_version
            ).first()
            
            self.model_b = db.query(MLModel).filter(
                MLModel.version == self.model_b_version
            ).first()
            
            if not self.model_a:
                raise ValueError(f"Model A not found: {self.model_a_version}")
            
            if not self.model_b:
                raise ValueError(f"Model B not found: {self.model_b_version}")
        
        # Load trainers
        self.trainer_a = AdvancedMLTrainer()
        self.trainer_a.load_model(self.model_a.model_path)
        
        self.trainer_b = AdvancedMLTrainer()
        self.trainer_b.load_model(self.model_b.model_path)
        
        logger.info(f"Loaded models for A/B test: {self.model_a_version} vs {self.model_b_version}")
    
    def assign_variant(self, signal_id: int) -> str:
        """
        Assign signal to a variant (A or B) using consistent hashing.
        
        Args:
            signal_id: Signal ID
            
        Returns:
            'A' or 'B'
        """
        # Hash signal ID to get consistent assignment
        hash_value = int(hashlib.md5(str(signal_id).encode()).hexdigest(), 16)
        normalized = (hash_value % 10000) / 10000.0
        
        return 'B' if normalized < self.traffic_split else 'A'
    
    def predict(self, signal_id: int, features: Dict[str, float]) -> Tuple[int, float, str]:
        """
        Make prediction using assigned variant.
        
        Args:
            signal_id: Signal ID
            features: Feature dict
            
        Returns:
            Tuple of (prediction, probability, variant)
        """
        variant = self.assign_variant(signal_id)
        
        if variant == 'A':
            prediction, probability = self.trainer_a.predict(features)
        else:
            prediction, probability = self.trainer_b.predict(features)
        
        return prediction, probability, variant
    
    def compare_performance(self, days_back: int = 7, min_samples: int = 20) -> Dict:
        """
        Compare performance of both models.
        
        Args:
            days_back: Number of days to analyze
            min_samples: Minimum samples per variant
            
        Returns:
            Dict with comparison results
        """
        with get_db_context() as db:
            # Get signals with predictions and outcomes
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            
            signals = db.query(Signal).filter(
                Signal.created_at >= cutoff,
                Signal.y_beat.isnot(None),
                Signal.features.isnot(None)
            ).all()
            
            # Separate by variant
            variant_a_signals = []
            variant_b_signals = []
            
            for signal in signals:
                variant = self.assign_variant(signal.id)
                if variant == 'A':
                    variant_a_signals.append(signal)
                else:
                    variant_b_signals.append(signal)
            
            if len(variant_a_signals) < min_samples or len(variant_b_signals) < min_samples:
                return {
                    'status': 'insufficient_data',
                    'variant_a_samples': len(variant_a_signals),
                    'variant_b_samples': len(variant_b_signals),
                    'min_samples': min_samples
                }
            
            # Calculate metrics for each variant
            metrics_a = self._calculate_metrics(variant_a_signals, self.trainer_a)
            metrics_b = self._calculate_metrics(variant_b_signals, self.trainer_b)
            
            # Statistical significance test
            significance = self._test_significance(
                metrics_a['accuracy'],
                metrics_b['accuracy'],
                len(variant_a_signals),
                len(variant_b_signals)
            )
            
            # Determine winner
            winner = None
            if significance['is_significant']:
                if metrics_b['accuracy'] > metrics_a['accuracy']:
                    winner = 'B'
                else:
                    winner = 'A'
            
            return {
                'status': 'success',
                'test_name': self.name,
                'days_back': days_back,
                'variant_a': {
                    'model_version': self.model_a_version,
                    'num_samples': len(variant_a_signals),
                    'metrics': metrics_a
                },
                'variant_b': {
                    'model_version': self.model_b_version,
                    'num_samples': len(variant_b_signals),
                    'metrics': metrics_b
                },
                'significance': significance,
                'winner': winner,
                'recommendation': self._get_recommendation(winner, significance),
                'calculated_at': datetime.utcnow().isoformat()
            }
    
    def _calculate_metrics(self, signals: List[Signal], trainer: AdvancedMLTrainer) -> Dict:
        """Calculate metrics for a set of signals."""
        predictions = []
        actuals = []
        probabilities = []
        
        for signal in signals:
            features = signal.features or {}
            prediction, probability = trainer.predict(features)
            
            predictions.append(prediction)
            actuals.append(signal.y_beat)
            probabilities.append(probability)
        
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        probabilities = np.array(probabilities)
        
        accuracy = (predictions == actuals).mean()
        
        # Precision
        true_positives = ((predictions == 1) & (actuals == 1)).sum()
        false_positives = ((predictions == 1) & (actuals == 0)).sum()
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        
        # Recall
        false_negatives = ((predictions == 0) & (actuals == 1)).sum()
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        # F1
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Average confidence
        avg_confidence = probabilities.mean()
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'avg_confidence': float(avg_confidence)
        }
    
    def _test_significance(
        self,
        accuracy_a: float,
        accuracy_b: float,
        n_a: int,
        n_b: int,
        alpha: float = 0.05
    ) -> Dict:
        """
        Test statistical significance using two-proportion z-test.
        
        Args:
            accuracy_a: Accuracy of variant A
            accuracy_b: Accuracy of variant B
            n_a: Sample size of variant A
            n_b: Sample size of variant B
            alpha: Significance level
            
        Returns:
            Dict with significance test results
        """
        from scipy import stats
        
        # Two-proportion z-test
        p_pooled = (accuracy_a * n_a + accuracy_b * n_b) / (n_a + n_b)
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_a + 1/n_b))
        
        if se == 0:
            return {
                'is_significant': False,
                'p_value': 1.0,
                'z_score': 0.0,
                'alpha': alpha
            }
        
        z_score = (accuracy_b - accuracy_a) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        return {
            'is_significant': p_value < alpha,
            'p_value': float(p_value),
            'z_score': float(z_score),
            'alpha': alpha,
            'confidence_level': 1 - alpha
        }
    
    def _get_recommendation(self, winner: Optional[str], significance: Dict) -> str:
        """Get recommendation based on test results."""
        if not significance['is_significant']:
            return "Continue test - no significant difference detected"
        
        if winner == 'A':
            return f"Keep model A ({self.model_a_version}) - performs better"
        elif winner == 'B':
            return f"Switch to model B ({self.model_b_version}) - performs better"
        else:
            return "Continue test - inconclusive results"
    
    def get_traffic_distribution(self, days_back: int = 7) -> Dict:
        """
        Get actual traffic distribution between variants.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dict with traffic distribution
        """
        with get_db_context() as db:
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            
            signals = db.query(Signal).filter(
                Signal.created_at >= cutoff
            ).all()
            
            variant_a_count = 0
            variant_b_count = 0
            
            for signal in signals:
                variant = self.assign_variant(signal.id)
                if variant == 'A':
                    variant_a_count += 1
                else:
                    variant_b_count += 1
            
            total = variant_a_count + variant_b_count
            
            return {
                'total_signals': total,
                'variant_a_count': variant_a_count,
                'variant_b_count': variant_b_count,
                'variant_a_percentage': (variant_a_count / total * 100) if total > 0 else 0,
                'variant_b_percentage': (variant_b_count / total * 100) if total > 0 else 0,
                'expected_split': self.traffic_split * 100,
                'days_back': days_back
            }

