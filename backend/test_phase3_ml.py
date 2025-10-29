"""
Test script for Phase 3 ML enhancements.

Tests:
1. Advanced ML models training
2. Feature engineering
3. FinBERT sentiment analysis
4. Model explainability (SHAP)
5. ML API endpoints
"""
import sys
import logging
from datetime import datetime
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_feature_engineering():
    """Test feature engineering module."""
    logger.info("=" * 60)
    logger.info("TEST 1: Feature Engineering")
    logger.info("=" * 60)
    
    from app.ml.feature_engineering import FeatureEngineer
    
    engineer = FeatureEngineer()
    
    # Test technical indicators
    logger.info("Testing technical indicators for AAPL...")
    technical = engineer.add_technical_indicators("AAPL", period="1mo")
    logger.info(f"Technical indicators: {list(technical.keys())}")
    logger.info(f"RSI: {technical['rsi']:.2f}")
    logger.info(f"MACD: {technical['macd']:.4f}")
    logger.info(f"BB Position: {technical['bb_position']:.2f}")
    
    # Test sentiment aggregation
    logger.info("\nTesting sentiment aggregation...")
    sentiment_agg = engineer.add_sentiment_aggregation(
        sentiment=0.8,
        magnitude=4.5,
        credibility=5.0
    )
    logger.info(f"Sentiment aggregation: {sentiment_agg}")
    
    # Test temporal features
    logger.info("\nTesting temporal features...")
    temporal = engineer.add_temporal_features()
    logger.info(f"Temporal features: {temporal}")
    
    # Test interaction features
    logger.info("\nTesting interaction features...")
    base_features = {
        'sentiment': 0.8,
        'vol_z': 2.5,
        'ret_1d': 0.03,
        'novelty': 5.0,
        'credibility': 5.0,
        'rsi': 65.0,
        'macd_diff': 0.5,
        'gap_pct': 0.02
    }
    interactions = engineer.add_interaction_features(base_features)
    logger.info(f"Interaction features: {interactions}")
    
    logger.info("✅ Feature engineering test passed!\n")
    return True


def test_finbert_sentiment():
    """Test FinBERT sentiment analysis."""
    logger.info("=" * 60)
    logger.info("TEST 2: FinBERT Sentiment Analysis")
    logger.info("=" * 60)
    
    from app.core.sentiment_advanced import (
        analyze_finbert_sentiment,
        analyze_combined_sentiment,
        batch_analyze_sentiment
    )
    
    # Test single text
    text = "Apple reports record quarterly earnings, beating analyst expectations by 15%"
    
    logger.info(f"Analyzing: '{text}'")
    
    # FinBERT only
    logger.info("\nFinBERT analysis:")
    finbert_result = analyze_finbert_sentiment(text)
    logger.info(f"  Sentiment: {finbert_result['sentiment']:.3f}")
    logger.info(f"  Label: {finbert_result['label']}")
    logger.info(f"  Confidence: {finbert_result['confidence']:.3f}")
    
    # Combined VADER + FinBERT
    logger.info("\nCombined analysis:")
    combined_result = analyze_combined_sentiment(text)
    logger.info(f"  Combined sentiment: {combined_result['sentiment']:.3f}")
    logger.info(f"  VADER score: {combined_result['vader_score']:.3f}")
    logger.info(f"  FinBERT score: {combined_result['finbert_score']:.3f}")
    logger.info(f"  Confidence: {combined_result['confidence']:.3f}")
    
    # Batch analysis
    logger.info("\nBatch analysis:")
    texts = [
        "Stock price surges on positive earnings report",
        "Company faces bankruptcy amid mounting losses",
        "Quarterly results meet expectations"
    ]
    batch_results = batch_analyze_sentiment(texts)
    for i, (text, result) in enumerate(zip(texts, batch_results)):
        logger.info(f"  {i+1}. '{text[:50]}...'")
        logger.info(f"     Sentiment: {result['sentiment']:.3f}, Label: {result['label']}")
    
    logger.info("✅ FinBERT sentiment test passed!\n")
    return True


def test_advanced_models():
    """Test advanced ML models."""
    logger.info("=" * 60)
    logger.info("TEST 3: Advanced ML Models")
    logger.info("=" * 60)
    
    from app.ml.advanced_models import AdvancedMLTrainer
    from app.core.db import get_db_context
    from app.models.signal import Signal
    
    # Get labeled signals from database
    logger.info("Loading labeled signals from database...")
    with get_db_context() as db:
        signals = db.query(Signal).filter(Signal.y_beat.isnot(None)).limit(100).all()
    
    if len(signals) < 20:
        logger.warning(f"⚠️  Only {len(signals)} labeled signals found. Skipping model training test.")
        logger.info("   (Need at least 20 labeled signals to test training)")
        return True
    
    logger.info(f"Found {len(signals)} labeled signals")
    
    # Initialize trainer
    trainer = AdvancedMLTrainer()
    
    # Prepare data
    logger.info("Preparing training data...")
    X_train, X_test, y_train, y_test = trainer.prepare_data(signals, test_size=0.3)
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    logger.info(f"Class balance: {y_train.mean():.3f}")
    
    # Train models (without hyperparameter tuning for speed)
    logger.info("\nTraining Random Forest...")
    trainer.train_random_forest(X_train, y_train, tune_hyperparams=False)
    
    logger.info("Training XGBoost...")
    trainer.train_xgboost(X_train, y_train, tune_hyperparams=False)
    
    logger.info("Training LightGBM...")
    trainer.train_lightgbm(X_train, y_train, tune_hyperparams=False)
    
    # Compare models
    logger.info("\nComparing models...")
    comparison = trainer.compare_models(X_test, y_test)
    
    logger.info(f"\nBest model: {comparison['best_model']}")
    logger.info("\nAll results:")
    for result in comparison['all_results']:
        logger.info(f"  {result['model_name']}:")
        logger.info(f"    Accuracy: {result['accuracy']:.4f}")
        logger.info(f"    Precision: {result['precision']:.4f}")
        logger.info(f"    Recall: {result['recall']:.4f}")
        logger.info(f"    F1: {result['f1']:.4f}")
        logger.info(f"    ROC AUC: {result['roc_auc']:.4f}")
    
    # Get feature importance
    logger.info("\nFeature importance:")
    importance = trainer.get_feature_importance()
    for i, (feature, imp) in enumerate(list(importance.items())[:10]):
        logger.info(f"  {i+1}. {feature}: {imp:.4f}")
    
    # Test prediction
    logger.info("\nTesting prediction...")
    test_features = {col: 0.0 for col in trainer.feature_cols}
    test_features['sentiment'] = 0.8
    test_features['magnitude'] = 4.5
    test_features['credibility'] = 5.0
    
    prediction, probability = trainer.predict(test_features)
    logger.info(f"Prediction: {prediction} (probability: {probability:.3f})")
    
    logger.info("✅ Advanced ML models test passed!\n")
    return True


def test_explainability():
    """Test model explainability with SHAP."""
    logger.info("=" * 60)
    logger.info("TEST 4: Model Explainability (SHAP)")
    logger.info("=" * 60)
    
    from app.ml.advanced_models import AdvancedMLTrainer
    from app.ml.explainability import ModelExplainer
    from app.core.db import get_db_context
    from app.models.signal import Signal
    
    # Get labeled signals
    logger.info("Loading labeled signals...")
    with get_db_context() as db:
        signals = db.query(Signal).filter(Signal.y_beat.isnot(None)).limit(100).all()
    
    if len(signals) < 20:
        logger.warning(f"⚠️  Only {len(signals)} labeled signals found. Skipping explainability test.")
        return True
    
    # Train a simple model
    logger.info("Training model for explainability...")
    trainer = AdvancedMLTrainer()
    X_train, X_test, y_train, y_test = trainer.prepare_data(signals, test_size=0.3)
    trainer.train_random_forest(X_train, y_train, tune_hyperparams=False)
    
    # Create explainer
    logger.info("Creating SHAP explainer...")
    explainer = ModelExplainer(trainer)
    explainer.create_explainer(X_train)
    
    # Calculate SHAP values
    logger.info("Calculating SHAP values...")
    shap_values = explainer.explain_predictions(X_test[:10])  # Only first 10 for speed
    
    # Get feature importance
    logger.info("\nGlobal feature importance (SHAP):")
    importance = explainer.get_feature_importance(shap_values, top_n=10)
    for i, (feature, imp) in enumerate(importance.items()):
        logger.info(f"  {i+1}. {feature}: {imp:.4f}")
    
    # Explain single prediction
    logger.info("\nExplaining single prediction...")
    test_features = {col: 0.0 for col in trainer.feature_cols}
    test_features['sentiment'] = 0.8
    test_features['magnitude'] = 4.5
    test_features['credibility'] = 5.0
    
    explanation = explainer.explain_single_prediction(test_features, top_n=5)
    logger.info(f"Prediction: {explanation['prediction']} (prob: {explanation['probability']:.3f})")
    logger.info(f"Base value: {explanation['base_value']:.3f}")
    logger.info("Top contributing features:")
    for contrib in explanation['top_contributions']:
        logger.info(f"  {contrib['feature']}: {contrib['contribution']:+.4f} (value: {contrib['value']:.2f})")
    
    logger.info("✅ Model explainability test passed!\n")
    return True


def test_training_pipeline():
    """Test full training pipeline."""
    logger.info("=" * 60)
    logger.info("TEST 5: Full Training Pipeline")
    logger.info("=" * 60)
    
    from app.ml.training_pipeline import MLTrainingPipeline
    from app.core.db import get_db_context
    from app.models.signal import Signal
    
    # Check if we have enough data
    logger.info("Checking for labeled signals...")
    with get_db_context() as db:
        count = db.query(Signal).filter(Signal.y_beat.isnot(None)).count()
    
    if count < 20:
        logger.warning(f"⚠️  Only {count} labeled signals found. Skipping pipeline test.")
        logger.info("   (Need at least 20 labeled signals to test pipeline)")
        return True
    
    logger.info(f"Found {count} labeled signals")
    
    # Create pipeline
    logger.info("Creating training pipeline...")
    pipeline = MLTrainingPipeline(
        use_feature_engineering=False,  # Skip for speed
        tune_hyperparams=False
    )
    
    # Run pipeline
    logger.info("Running full pipeline...")
    try:
        results = pipeline.run_full_pipeline(
            min_samples=20,
            model_types=['random_forest', 'xgboost']  # Only 2 models for speed
        )
        
        logger.info(f"\nPipeline completed successfully!")
        logger.info(f"Version: {results['version']}")
        logger.info(f"Model ID: {results['model_id']}")
        logger.info(f"Model type: {results['model_type']}")
        logger.info(f"Training samples: {results['training_samples']}")
        logger.info(f"Test samples: {results['test_samples']}")
        logger.info(f"Metrics: {results['metrics']}")
        
        logger.info("✅ Training pipeline test passed!\n")
        return True
    
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 3 ML ENHANCEMENTS - TEST SUITE")
    logger.info("=" * 60 + "\n")
    
    tests = [
        ("Feature Engineering", test_feature_engineering),
        ("FinBERT Sentiment", test_finbert_sentiment),
        ("Advanced ML Models", test_advanced_models),
        ("Model Explainability", test_explainability),
        ("Training Pipeline", test_training_pipeline),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"❌ {name} test failed with exception: {e}", exc_info=True)
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("\n🎉 All tests passed!")
        return 0
    else:
        logger.info(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

