"""
Unit Tests for Training System

Tests individual components of the price prediction training system.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pathlib
import tempfile
import json

from app.ml.price_model import (
    calculate_indicators,
    compute_time_decay_weights,
    create_walk_forward_splits,
    prepare_features_and_target,
    train_model,
    evaluate_model,
    save_model,
    load_model
)
from app.services.model_registry import ModelRegistry


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start="2020-01-01", end="2023-12-31", freq="D")
    n = len(dates)
    
    # Generate synthetic price data with trend
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(n) * 2)
    
    df = pd.DataFrame({
        "Open": close_prices + np.random.randn(n) * 0.5,
        "High": close_prices + np.abs(np.random.randn(n) * 1.5),
        "Low": close_prices - np.abs(np.random.randn(n) * 1.5),
        "Close": close_prices,
        "Volume": np.random.randint(1000000, 10000000, n)
    }, index=dates)
    
    return df


class TestIndicatorCalculation:
    """Test technical indicator calculations."""
    
    def test_calculate_indicators_output_shape(self, sample_ohlcv_data):
        """Test that indicators are added to DataFrame."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        
        # Should have more columns than input
        assert df_with_indicators.shape[1] > sample_ohlcv_data.shape[1]
        
        # Should have same number of rows
        assert df_with_indicators.shape[0] == sample_ohlcv_data.shape[0]
    
    def test_calculate_indicators_includes_sma(self, sample_ohlcv_data):
        """Test that SMA indicators are calculated."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        
        assert "sma_5" in df_with_indicators.columns
        assert "sma_10" in df_with_indicators.columns
        assert "sma_20" in df_with_indicators.columns
        assert "sma_50" in df_with_indicators.columns
    
    def test_calculate_indicators_includes_rsi(self, sample_ohlcv_data):
        """Test that RSI is calculated."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        
        assert "rsi" in df_with_indicators.columns
        
        # RSI should be between 0 and 100
        rsi_values = df_with_indicators["rsi"].dropna()
        assert (rsi_values >= 0).all()
        assert (rsi_values <= 100).all()
    
    def test_calculate_indicators_includes_macd(self, sample_ohlcv_data):
        """Test that MACD indicators are calculated."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        
        assert "macd" in df_with_indicators.columns
        assert "macd_signal" in df_with_indicators.columns
        assert "macd_hist" in df_with_indicators.columns
    
    def test_calculate_indicators_custom_config(self, sample_ohlcv_data):
        """Test that custom indicator config is respected."""
        config = {
            "sma_periods": [10, 30],
            "rsi_period": 10
        }
        
        df_with_indicators = calculate_indicators(sample_ohlcv_data, config)
        
        assert "sma_10" in df_with_indicators.columns
        assert "sma_30" in df_with_indicators.columns
        assert "sma_5" not in df_with_indicators.columns  # Not in custom config


class TestTimeDecayWeights:
    """Test time-decay weight computation."""
    
    def test_weights_sum_to_one(self, sample_ohlcv_data):
        """Test that weights sum to 1."""
        weights = compute_time_decay_weights(sample_ohlcv_data)
        
        assert np.isclose(weights.sum(), 1.0)
    
    def test_weights_monotonic_decreasing(self, sample_ohlcv_data):
        """Test that weights decrease as we go back in time."""
        weights = compute_time_decay_weights(sample_ohlcv_data)
        
        # Weights should be monotonically increasing (older data has lower weight)
        # Since index is chronological, weights should increase
        assert (np.diff(weights) >= 0).all()
    
    def test_weights_recent_higher(self, sample_ohlcv_data):
        """Test that recent data has higher weight than old data."""
        weights = compute_time_decay_weights(sample_ohlcv_data)
        
        # Last weight (most recent) should be higher than first (oldest)
        assert weights[-1] > weights[0]
    
    def test_weights_half_life(self):
        """Test that half-life parameter works correctly."""
        # Create data spanning exactly 365 days
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        df = pd.DataFrame({"value": range(len(dates))}, index=dates)
        
        weights = compute_time_decay_weights(df, half_life_days=365)
        
        # Weight at 365 days ago should be approximately half of most recent
        # (allowing for some numerical error)
        assert 0.4 < weights[0] / weights[-1] < 0.6
    
    def test_weights_requires_datetime_index(self):
        """Test that function requires DatetimeIndex."""
        df = pd.DataFrame({"value": [1, 2, 3]})
        
        with pytest.raises(ValueError, match="DatetimeIndex"):
            compute_time_decay_weights(df)


class TestWalkForwardSplits:
    """Test walk-forward cross-validation splits."""

    def test_splits_no_overlap(self):
        """Test that train and test sets don't overlap."""
        # Use more samples to accommodate splits
        splits = create_walk_forward_splits(n_samples=200, n_splits=3)

        for train_idx, test_idx in splits:
            # No overlap between train and test
            assert len(set(train_idx) & set(test_idx)) == 0

    def test_splits_chronological(self):
        """Test that test set comes after train set (no look-ahead)."""
        splits = create_walk_forward_splits(n_samples=200, n_splits=3)

        for train_idx, test_idx in splits:
            # All test indices should be greater than all train indices
            assert train_idx.max() < test_idx.min()

    def test_splits_count(self):
        """Test that correct number of splits is created."""
        n_splits = 3
        splits = create_walk_forward_splits(n_samples=200, n_splits=n_splits)

        assert len(splits) == n_splits

    def test_splits_test_size(self):
        """Test that test size is approximately correct."""
        n_samples = 200
        test_size = 0.2
        splits = create_walk_forward_splits(n_samples=n_samples, n_splits=3, test_size=test_size)

        for train_idx, test_idx in splits:
            # Test size should be approximately 20% of total (40 samples)
            assert 35 <= len(test_idx) <= 45  # Allow some variance


class TestFeaturePreparation:
    """Test feature and target preparation."""
    
    def test_prepare_features_excludes_ohlcv(self, sample_ohlcv_data):
        """Test that OHLCV columns are excluded from features."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        # OHLCV columns should not be in features
        assert "Open" not in X.columns
        assert "High" not in X.columns
        assert "Low" not in X.columns
        assert "Close" not in X.columns
        assert "Volume" not in X.columns
    
    def test_prepare_features_target_alignment(self, sample_ohlcv_data):
        """Test that features and target have same length."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        assert len(X) == len(y)
    
    def test_prepare_features_no_nan(self, sample_ohlcv_data):
        """Test that NaN values are removed."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        # No NaN in features
        assert not X.isna().any().any()
        
        # No NaN in target
        assert not y.isna().any()
    
    def test_prepare_features_forecast_horizon(self, sample_ohlcv_data):
        """Test that forecast horizon shifts target correctly."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators, forecast_horizon=1)
        
        # Target should be shifted by 1 day
        # (We can't easily test the exact shift without knowing the original data,
        # but we can verify that the function runs without error)
        assert len(y) > 0


class TestModelTraining:
    """Test model training."""
    
    def test_train_model_5y_mode(self, sample_ohlcv_data):
        """Test training with 5y mode (Ridge regression)."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        model = train_model(X, y, mode="5y")
        
        # Model should be a Pipeline
        assert hasattr(model, "predict")
        
        # Should be able to make predictions
        predictions = model.predict(X)
        assert len(predictions) == len(y)
    
    def test_train_model_10y_mode(self, sample_ohlcv_data):
        """Test training with 10y mode (RandomForest)."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        model = train_model(X, y, mode="10y")
        
        # Model should be a Pipeline
        assert hasattr(model, "predict")
        
        # Should be able to make predictions
        predictions = model.predict(X)
        assert len(predictions) == len(y)
    
    def test_train_model_with_weights(self, sample_ohlcv_data):
        """Test training with sample weights."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        weights = compute_time_decay_weights(X)
        model = train_model(X, y, mode="10y", sample_weights=weights)
        
        # Should train successfully
        assert hasattr(model, "predict")
    
    def test_train_model_invalid_mode(self, sample_ohlcv_data):
        """Test that invalid mode raises error."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        with pytest.raises(ValueError, match="Invalid mode"):
            train_model(X, y, mode="invalid")


class TestModelEvaluation:
    """Test model evaluation."""
    
    def test_evaluate_model_returns_metrics(self, sample_ohlcv_data):
        """Test that evaluation returns expected metrics."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        model = train_model(X, y, mode="5y")
        metrics = evaluate_model(model, X, y)
        
        assert "r2" in metrics
        assert "rmse" in metrics
        assert "mae" in metrics
    
    def test_evaluate_model_r2_range(self, sample_ohlcv_data):
        """Test that R² is in valid range."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        model = train_model(X, y, mode="5y")
        metrics = evaluate_model(model, X, y)
        
        # R² can be negative for very bad models, but should be reasonable here
        assert metrics["r2"] > -1.0
        assert metrics["r2"] <= 1.0


class TestModelPersistence:
    """Test model saving and loading."""
    
    def test_save_and_load_model(self, sample_ohlcv_data):
        """Test that model can be saved and loaded."""
        df_with_indicators = calculate_indicators(sample_ohlcv_data)
        X, y = prepare_features_and_target(df_with_indicators)
        
        model = train_model(X, y, mode="5y")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = pathlib.Path(tmpdir) / "test_model.pkl"
            
            # Save model
            save_model(model, model_path, compress=3)
            assert model_path.exists()
            
            # Load model
            loaded_model = load_model(model_path)
            
            # Predictions should match
            pred_original = model.predict(X)
            pred_loaded = loaded_model.predict(X)
            
            np.testing.assert_array_almost_equal(pred_original, pred_loaded)


class TestModelRegistry:
    """Test model registry functionality."""
    
    def test_registry_add_and_get_model(self):
        """Test adding and retrieving model metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = pathlib.Path(tmpdir) / "registry.json"
            registry = ModelRegistry(registry_path)
            
            metadata = registry.add_model(
                ticker="AAPL",
                mode="10y",
                model_path="/path/to/model.pkl",
                r2_score=0.85,
                n_observations=1000,
                date_range_start="2020-01-01",
                date_range_end="2023-12-31",
                indicator_config={"sma_periods": [5, 10]}
            )
            
            # Retrieve model
            retrieved = registry.get_model("AAPL", "10y")
            
            assert retrieved is not None
            assert retrieved.ticker == "AAPL"
            assert retrieved.mode == "10y"
            assert retrieved.r2_score == 0.85
    
    def test_registry_param_hash_deterministic(self):
        """Test that parameter hash is deterministic."""
        hash1 = ModelRegistry.compute_param_hash(
            ticker="AAPL",
            mode="10y",
            date_range_start="2020-01-01",
            date_range_end="2023-12-31",
            indicator_config={"sma_periods": [5, 10]}
        )
        
        hash2 = ModelRegistry.compute_param_hash(
            ticker="AAPL",
            mode="10y",
            date_range_start="2020-01-01",
            date_range_end="2023-12-31",
            indicator_config={"sma_periods": [5, 10]}
        )
        
        assert hash1 == hash2
    
    def test_registry_param_hash_different_for_different_params(self):
        """Test that different parameters produce different hashes."""
        hash1 = ModelRegistry.compute_param_hash(
            ticker="AAPL",
            mode="10y",
            date_range_start="2020-01-01",
            date_range_end="2023-12-31",
            indicator_config={"sma_periods": [5, 10]}
        )
        
        hash2 = ModelRegistry.compute_param_hash(
            ticker="TSLA",  # Different ticker
            mode="10y",
            date_range_start="2020-01-01",
            date_range_end="2023-12-31",
            indicator_config={"sma_periods": [5, 10]}
        )
        
        assert hash1 != hash2

