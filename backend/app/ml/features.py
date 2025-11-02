"""
Feature engineering for research model.

Single source of truth for feature extraction - used consistently
for both online prediction and offline training.
"""
from typing import Dict, Any, Optional


# Numeric features to extract
NUMERIC_FEATURES = [
    "rsi14",
    "atr14",
    "gap_pct",
    "vwap_dev_pct",
    "volume_spike_x",
    "llm_confidence",
    "trust_score",
    "novelty_score",
]

# Categorical features to extract
CATEGORICAL_FEATURES = [
    "catalyst_type",
    "stance",
    "sector",
]


def featurize(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize features from analysis payload.
    
    Args:
        analysis: Dict containing technical indicators, LLM outputs, etc.
        
    Returns:
        Dict of normalized features ready for model input
    """
    features: Dict[str, Any] = {}
    
    # Extract numeric features
    for key in NUMERIC_FEATURES:
        value = analysis.get(key)
        if value is not None:
            try:
                features[key] = float(value)
            except (ValueError, TypeError):
                pass  # Skip invalid values
    
    # Derive relative features from SMAs
    sma20 = analysis.get("sma20")
    sma50 = analysis.get("sma50")
    close = analysis.get("adj_close")
    
    if sma20 is not None and close is not None:
        try:
            sma20_f = float(sma20)
            close_f = float(close)
            if sma20_f != 0:
                features["sma20_dev_pct"] = 100 * (close_f - sma20_f) / sma20_f
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    
    if sma50 is not None and close is not None:
        try:
            sma50_f = float(sma50)
            close_f = float(close)
            if sma50_f != 0:
                features["sma50_dev_pct"] = 100 * (close_f - sma50_f) / sma50_f
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    
    # Extract categorical features
    for key in CATEGORICAL_FEATURES:
        value = analysis.get(key)
        if value is not None:
            features[key] = str(value)
    
    # Clamp probability features to [0, 1]
    if "llm_confidence" in features:
        features["llm_confidence"] = max(0.0, min(1.0, features["llm_confidence"]))
    
    if "trust_score" in features:
        features["trust_score"] = max(0.0, min(1.0, features["trust_score"]))
    
    if "novelty_score" in features:
        features["novelty_score"] = max(0.0, min(1.0, features["novelty_score"]))
    
    return features


def validate_features(features: Dict[str, Any]) -> bool:
    """
    Check if features dict has minimum required fields.
    
    Args:
        features: Feature dict from featurize()
        
    Returns:
        True if features are valid for model input
    """
    # Require at least some numeric features
    has_numeric = any(k in features for k in NUMERIC_FEATURES)
    
    # Require at least one categorical
    has_categorical = any(k in features for k in CATEGORICAL_FEATURES)
    
    return has_numeric and has_categorical

