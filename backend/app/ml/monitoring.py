"""
Model monitoring and drift detection.

Tracks model performance, prediction accuracy, and data drift over time.
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import numpy as np
from app.core.db import get_db_context
from app.models.signal import Signal
from app.models.ml_model import MLModel

logger = logging.getLogger(__name__)


class ModelMonitor:
    """
    Monitor ML model performance and detect drift.
    
    Tracks:
    - Prediction accuracy over time
    - Feature distribution drift
    - Model performance degradation
    - Prediction confidence trends
    """
    
    def __init__(self, model_version: Optional[str] = None):
        """
        Initialize model monitor.
        
        Args:
            model_version: Model version to monitor (None = active model)
        """
        self.model_version = model_version
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load model from database."""
        with get_db_context() as db:
            if self.model_version:
                self.model = db.query(MLModel).filter(
                    MLModel.version == self.model_version
                ).first()
            else:
                self.model = db.query(MLModel).filter(
                    MLModel.is_active == True
                ).first()
            
            if not self.model:
                raise ValueError(f"Model not found: {self.model_version or 'active'}")
    
    def calculate_accuracy(
        self,
        days_back: int = 7,
        min_samples: int = 10
    ) -> Dict:
        """
        Calculate model accuracy on recent predictions.
        
        Args:
            days_back: Number of days to look back
            min_samples: Minimum samples required
            
        Returns:
            Dict with accuracy metrics
        """
        with get_db_context() as db:
            # Get signals with predictions and actual outcomes
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            signals = db.query(Signal).filter(
                Signal.created_at >= cutoff,
                Signal.y_beat.isnot(None),  # Has actual outcome
                Signal.features.isnot(None)  # Has features (predictions)
            ).all()
            
            if len(signals) < min_samples:
                return {
                    'status': 'insufficient_data',
                    'num_samples': len(signals),
                    'min_samples': min_samples
                }
            
            # Extract predictions and actuals
            predictions = []
            actuals = []
            
            for signal in signals:
                features = signal.features or {}
                if 'ml_prediction' in features:
                    predictions.append(features['ml_prediction'])
                    actuals.append(signal.y_beat)
            
            if len(predictions) < min_samples:
                return {
                    'status': 'insufficient_predictions',
                    'num_predictions': len(predictions),
                    'min_samples': min_samples
                }
            
            # Calculate metrics
            predictions = np.array(predictions)
            actuals = np.array(actuals)
            
            accuracy = (predictions == actuals).mean()
            precision = self._calculate_precision(predictions, actuals)
            recall = self._calculate_recall(predictions, actuals)
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            return {
                'status': 'success',
                'model_version': self.model.version,
                'days_back': days_back,
                'num_samples': len(predictions),
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1),
                'calculated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def _calculate_precision(self, predictions: np.ndarray, actuals: np.ndarray) -> float:
        """Calculate precision."""
        true_positives = ((predictions == 1) & (actuals == 1)).sum()
        false_positives = ((predictions == 1) & (actuals == 0)).sum()
        
        if true_positives + false_positives == 0:
            return 0.0
        
        return true_positives / (true_positives + false_positives)
    
    def _calculate_recall(self, predictions: np.ndarray, actuals: np.ndarray) -> float:
        """Calculate recall."""
        true_positives = ((predictions == 1) & (actuals == 1)).sum()
        false_negatives = ((predictions == 0) & (actuals == 1)).sum()
        
        if true_positives + false_negatives == 0:
            return 0.0
        
        return true_positives / (true_positives + false_negatives)
    
    def detect_feature_drift(
        self,
        days_back: int = 7,
        reference_days: int = 30,
        threshold: float = 0.1
    ) -> Dict:
        """
        Detect feature distribution drift.
        
        Compares recent feature distributions to reference period.
        
        Args:
            days_back: Recent period to analyze
            reference_days: Reference period for comparison
            threshold: Drift threshold (0-1)
            
        Returns:
            Dict with drift detection results
        """
        with get_db_context() as db:
            # Get recent signals
            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
            recent_signals = db.query(Signal).filter(
                Signal.created_at >= recent_cutoff,
                Signal.features.isnot(None)
            ).all()

            # Get reference signals
            reference_cutoff = datetime.now(timezone.utc) - timedelta(days=reference_days)
            reference_end = datetime.now(timezone.utc) - timedelta(days=days_back)
            reference_signals = db.query(Signal).filter(
                Signal.created_at >= reference_cutoff,
                Signal.created_at < reference_end,
                Signal.features.isnot(None)
            ).all()
            
            if len(recent_signals) < 10 or len(reference_signals) < 10:
                return {
                    'status': 'insufficient_data',
                    'recent_samples': len(recent_signals),
                    'reference_samples': len(reference_signals)
                }
            
            # Extract features
            recent_features = self._extract_features(recent_signals)
            reference_features = self._extract_features(reference_signals)
            
            # Calculate drift for each feature
            drift_scores = {}
            drifted_features = []
            
            for feature_name in recent_features.keys():
                if feature_name in reference_features:
                    drift = self._calculate_drift(
                        recent_features[feature_name],
                        reference_features[feature_name]
                    )
                    drift_scores[feature_name] = drift
                    
                    if drift > threshold:
                        drifted_features.append({
                            'feature': feature_name,
                            'drift_score': drift,
                            'recent_mean': float(np.mean(recent_features[feature_name])),
                            'reference_mean': float(np.mean(reference_features[feature_name])),
                            'recent_std': float(np.std(recent_features[feature_name])),
                            'reference_std': float(np.std(reference_features[feature_name]))
                        })
            
            # Overall drift score (average of all features)
            overall_drift = np.mean(list(drift_scores.values())) if drift_scores else 0.0
            
            return {
                'status': 'success',
                'model_version': self.model.version,
                'days_back': days_back,
                'reference_days': reference_days,
                'recent_samples': len(recent_signals),
                'reference_samples': len(reference_signals),
                'overall_drift': float(overall_drift),
                'drift_threshold': threshold,
                'num_drifted_features': len(drifted_features),
                'drifted_features': drifted_features,
                'all_drift_scores': drift_scores,
                'calculated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def _extract_features(self, signals: List[Signal]) -> Dict[str, List[float]]:
        """Extract features from signals."""
        features = defaultdict(list)
        
        for signal in signals:
            signal_features = signal.features or {}
            for key, value in signal_features.items():
                if isinstance(value, (int, float)):
                    features[key].append(float(value))
        
        return dict(features)
    
    def _calculate_drift(self, recent: List[float], reference: List[float]) -> float:
        """
        Calculate drift score using Kolmogorov-Smirnov test.
        
        Returns value between 0 (no drift) and 1 (maximum drift).
        """
        from scipy import stats
        
        # KS test
        statistic, _ = stats.ks_2samp(recent, reference)
        
        return float(statistic)
    
    def get_prediction_confidence_trend(
        self,
        days_back: int = 30,
        bucket_size: int = 1
    ) -> Dict:
        """
        Get prediction confidence trend over time.
        
        Args:
            days_back: Number of days to analyze
            bucket_size: Size of time buckets in days
            
        Returns:
            Dict with confidence trend data
        """
        with get_db_context() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

            signals = db.query(Signal).filter(
                Signal.created_at >= cutoff,
                Signal.features.isnot(None)
            ).order_by(Signal.created_at).all()
            
            if not signals:
                return {
                    'status': 'no_data',
                    'num_samples': 0
                }
            
            # Group by time buckets
            buckets = defaultdict(list)
            
            for signal in signals:
                features = signal.features or {}
                if 'ml_probability' in features:
                    # Calculate bucket
                    days_ago = (datetime.now(timezone.utc) - signal.created_at).days
                    bucket = days_ago // bucket_size
                    
                    buckets[bucket].append(features['ml_probability'])
            
            # Calculate statistics for each bucket
            trend_data = []
            for bucket in sorted(buckets.keys(), reverse=True):
                confidences = buckets[bucket]
                trend_data.append({
                    'days_ago': bucket * bucket_size,
                    'num_predictions': len(confidences),
                    'mean_confidence': float(np.mean(confidences)),
                    'std_confidence': float(np.std(confidences)),
                    'min_confidence': float(np.min(confidences)),
                    'max_confidence': float(np.max(confidences))
                })
            
            return {
                'status': 'success',
                'model_version': self.model.version,
                'days_back': days_back,
                'bucket_size': bucket_size,
                'num_buckets': len(trend_data),
                'trend_data': trend_data,
                'calculated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def get_performance_summary(self, days_back: int = 7) -> Dict:
        """
        Get comprehensive performance summary.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dict with performance summary
        """
        accuracy_metrics = self.calculate_accuracy(days_back=days_back)
        drift_metrics = self.detect_feature_drift(days_back=days_back)
        confidence_trend = self.get_prediction_confidence_trend(days_back=days_back)
        
        # Determine health status
        health_status = 'healthy'
        warnings = []
        
        if accuracy_metrics.get('status') == 'success':
            if accuracy_metrics['accuracy'] < 0.6:
                health_status = 'degraded'
                warnings.append('Low accuracy')
        
        if drift_metrics.get('status') == 'success':
            if drift_metrics['overall_drift'] > 0.2:
                health_status = 'degraded'
                warnings.append('High feature drift')
            
            if drift_metrics['num_drifted_features'] > 3:
                warnings.append(f"{drift_metrics['num_drifted_features']} features drifted")
        
        return {
            'model_version': self.model.version,
            'health_status': health_status,
            'warnings': warnings,
            'days_back': days_back,
            'accuracy_metrics': accuracy_metrics,
            'drift_metrics': drift_metrics,
            'confidence_trend': confidence_trend,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

