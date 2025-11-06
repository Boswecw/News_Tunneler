"""
Integration Tests for Training System

Tests end-to-end training workflows with mocked yfinance data.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pathlib
import tempfile
from fastapi.testclient import TestClient

from app.main import app
from app.services.model_registry import ModelRegistry


@pytest.fixture
def mock_yfinance_data():
    """Create mock yfinance data for testing."""
    def _create_data(period="10y"):
        # Determine number of days based on period
        if period == "5y":
            days = 5 * 365
        elif period == "10y":
            days = 10 * 365
        else:
            days = 365
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq="D")
        n = len(dates)
        
        # Generate synthetic price data
        np.random.seed(42)
        close_prices = 100 + np.cumsum(np.random.randn(n) * 2)
        
        df = pd.DataFrame({
            "Date": dates,
            "Open": close_prices + np.random.randn(n) * 0.5,
            "High": close_prices + np.abs(np.random.randn(n) * 1.5),
            "Low": close_prices - np.abs(np.random.randn(n) * 1.5),
            "Close": close_prices,
            "Volume": np.random.randint(1000000, 10000000, n)
        })
        
        return df
    
    return _create_data


@pytest.fixture
def test_client():
    """Create test client for API testing."""
    return TestClient(app)


class TestTrainingEndToEnd:
    """Test complete training workflow."""
    
    @patch("app.api.training.yf.download")
    def test_train_5y_mode_retain_none(self, mock_download, mock_yfinance_data, test_client):
        """Test training with 5y mode and retain=none."""
        # Mock yfinance download
        mock_download.return_value = mock_yfinance_data("5y").set_index("Date")
        
        # Train model
        response = test_client.post(
            "/api/training/train/AAPL?mode=5y&retain=none&archive=false"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["ticker"] == "AAPL"
        assert data["mode"] == "5y"
        assert "model_path" in data
        assert "r2_score" in data
        assert "n_observations" in data
        assert "trained_at" in data
        assert "param_hash" in data
        
        # Verify model file was created
        model_path = pathlib.Path(data["model_path"])
        assert model_path.exists()
        
        # Verify data was pruned (retain=none)
        assert data["pruned_rows"] > 0
        
        # Cleanup
        if model_path.exists():
            model_path.unlink()
    
    @patch("app.api.training.yf.download")
    def test_train_10y_mode_retain_window(self, mock_download, mock_yfinance_data, test_client):
        """Test training with 10y mode and retain=window."""
        # Mock yfinance download
        mock_download.return_value = mock_yfinance_data("10y").set_index("Date")
        
        # Train model
        response = test_client.post(
            "/api/training/train/TSLA?mode=10y&retain=window&window_days=180&archive=false"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert data["ticker"] == "TSLA"
        assert data["mode"] == "10y"
        assert data["r2_score"] is not None
        
        # Verify model file was created
        model_path = pathlib.Path(data["model_path"])
        assert model_path.exists()
        
        # Cleanup
        if model_path.exists():
            model_path.unlink()
    
    @patch("app.api.training.yf.download")
    def test_train_with_archive(self, mock_download, mock_yfinance_data, test_client):
        """Test training with archive=true."""
        # Mock yfinance download
        mock_download.return_value = mock_yfinance_data("5y").set_index("Date")
        
        # Train model with archiving
        response = test_client.post(
            "/api/training/train/MSFT?mode=5y&retain=none&archive=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify archive was created
        assert data["archive_path"] is not None
        archive_path = pathlib.Path(data["archive_path"])
        assert archive_path.exists()
        assert archive_path.suffix == ".gz"
        
        # Cleanup
        model_path = pathlib.Path(data["model_path"])
        if model_path.exists():
            model_path.unlink()
        if archive_path.exists():
            archive_path.unlink()
    
    @patch("app.api.training.yf.download")
    def test_registry_updated_after_training(self, mock_download, mock_yfinance_data, test_client):
        """Test that registry is updated after training."""
        # Mock yfinance download
        mock_download.return_value = mock_yfinance_data("5y").set_index("Date")
        
        # Train model
        response = test_client.post(
            "/api/training/train/NVDA?mode=5y&retain=none&archive=false"
        )
        
        assert response.status_code == 200
        data = response.json()

        # Check registry (path relative to backend directory)
        registry = ModelRegistry(pathlib.Path("models/registry.json"))
        metadata = registry.get_model("NVDA", "5y")

        assert metadata is not None
        assert metadata.ticker == "NVDA"
        assert metadata.mode == "5y"
        assert metadata.param_hash == data["param_hash"]
        
        # Cleanup
        model_path = pathlib.Path(data["model_path"])
        if model_path.exists():
            model_path.unlink()


class TestPredictEndpoint:
    """Test prediction endpoint."""
    
    @patch("app.api.training.yf.download")
    def test_predict_after_training(self, mock_download, mock_yfinance_data, test_client):
        """Test that predict works after training."""
        # Mock yfinance download for both training and prediction
        mock_download.return_value = mock_yfinance_data("5y").set_index("Date")
        
        # Train model first
        train_response = test_client.post(
            "/api/training/train/GOOG?mode=5y&retain=none&archive=false"
        )
        assert train_response.status_code == 200
        
        # Now predict
        predict_response = test_client.get("/api/training/predict/GOOG?mode=5y")
        
        assert predict_response.status_code == 200
        data = predict_response.json()
        
        # Verify response structure
        assert data["ticker"] == "GOOG"
        assert data["mode"] == "5y"
        assert "predicted_close" in data
        assert "current_close" in data
        assert "predicted_change_pct" in data
        assert "model_trained_at" in data
        assert "features_snapshot" in data
        
        # Verify predicted_close is a number
        assert isinstance(data["predicted_close"], (int, float))
        assert data["predicted_close"] > 0
        
        # Cleanup
        model_path = pathlib.Path(train_response.json()["model_path"])
        if model_path.exists():
            model_path.unlink()
    
    def test_predict_without_training_returns_404(self, test_client):
        """Test that predict returns 404 for untrained ticker."""
        response = test_client.get("/api/training/predict/NOTRAINED?mode=5y")
        
        assert response.status_code == 404
        assert "No trained model found" in response.json()["detail"]


class TestPruneEndpoint:
    """Test prune endpoint."""
    
    @patch("app.api.training.yf.download")
    def test_prune_with_window(self, mock_download, mock_yfinance_data, test_client):
        """Test pruning with window retention."""
        # Mock yfinance download
        mock_download.return_value = mock_yfinance_data("10y").set_index("Date")
        
        # Train model with retain=all to populate database
        train_response = test_client.post(
            "/api/training/train/AMZN?mode=10y&retain=all&archive=false"
        )
        assert train_response.status_code == 200
        
        # Now prune to 90-day window
        prune_response = test_client.post(
            "/api/training/prune?retain=window&window_days=90"
        )
        
        assert prune_response.status_code == 200
        data = prune_response.json()
        
        # Verify response structure
        assert "pruned_rows" in data
        assert "retained_rows" in data
        assert "vacuum_completed" in data
        assert data["vacuum_completed"] is True
        
        # Should have pruned some rows
        assert data["pruned_rows"] > 0
        
        # Cleanup
        model_path = pathlib.Path(train_response.json()["model_path"])
        if model_path.exists():
            model_path.unlink()
    
    @patch("app.api.training.yf.download")
    def test_prune_with_none(self, mock_download, mock_yfinance_data, test_client):
        """Test pruning with none retention (delete all)."""
        # Mock yfinance download
        mock_download.return_value = mock_yfinance_data("5y").set_index("Date")
        
        # Train model with retain=all to populate database
        train_response = test_client.post(
            "/api/training/train/META?mode=5y&retain=all&archive=false"
        )
        assert train_response.status_code == 200
        
        # Now prune everything
        prune_response = test_client.post("/api/training/prune?retain=none")
        
        assert prune_response.status_code == 200
        data = prune_response.json()
        
        # Should have deleted all rows
        assert data["retained_rows"] == 0
        
        # Cleanup
        model_path = pathlib.Path(train_response.json()["model_path"])
        if model_path.exists():
            model_path.unlink()


class TestModelsEndpoint:
    """Test models list endpoint."""
    
    @patch("app.api.training.yf.download")
    def test_list_models_after_training(self, mock_download, mock_yfinance_data, test_client):
        """Test that models endpoint lists trained models."""
        # Mock yfinance download
        mock_download.return_value = mock_yfinance_data("5y").set_index("Date")
        
        # Train a model
        train_response = test_client.post(
            "/api/training/train/NFLX?mode=5y&retain=none&archive=false"
        )
        assert train_response.status_code == 200
        
        # List models
        list_response = test_client.get("/api/training/models")
        
        assert list_response.status_code == 200
        data = list_response.json()
        
        # Verify response structure
        assert "models" in data
        assert "total_count" in data
        assert isinstance(data["models"], list)
        
        # Should have at least one model
        assert data["total_count"] > 0
        
        # Find our trained model
        nflx_models = [m for m in data["models"] if m["ticker"] == "NFLX" and m["mode"] == "5y"]
        assert len(nflx_models) > 0
        
        # Verify model metadata
        model = nflx_models[0]
        assert "r2_score" in model
        assert "n_observations" in model
        assert "trained_at" in model
        assert "param_hash" in model
        
        # Cleanup
        model_path = pathlib.Path(train_response.json()["model_path"])
        if model_path.exists():
            model_path.unlink()
    
    def test_list_models_empty_registry(self, test_client):
        """Test that models endpoint works with empty registry."""
        # This test assumes a fresh registry or after cleanup
        # In practice, there might be models from other tests
        response = test_client.get("/api/training/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert "total_count" in data
        assert isinstance(data["models"], list)


class TestDeterminism:
    """Test reproducibility and determinism."""
    
    def test_param_hash_deterministic(self):
        """Test that parameter hash is deterministic."""
        from app.services.model_registry import ModelRegistry
        
        hash1 = ModelRegistry.compute_param_hash(
            ticker="AAPL",
            mode="10y",
            date_range_start="2020-01-01",
            date_range_end="2023-12-31",
            indicator_config={"sma_periods": [5, 10, 20]}
        )
        
        hash2 = ModelRegistry.compute_param_hash(
            ticker="AAPL",
            mode="10y",
            date_range_start="2020-01-01",
            date_range_end="2023-12-31",
            indicator_config={"sma_periods": [5, 10, 20]}
        )
        
        assert hash1 == hash2
    
    @patch("app.api.training.yf.download")
    def test_training_produces_consistent_hash(self, mock_download, mock_yfinance_data, test_client):
        """Test that training same ticker produces same hash."""
        # Mock yfinance download
        mock_data = mock_yfinance_data("5y").set_index("Date")
        mock_download.return_value = mock_data
        
        # Train model twice
        response1 = test_client.post(
            "/api/training/train/HASH_TEST?mode=5y&retain=none&archive=false"
        )
        assert response1.status_code == 200
        hash1 = response1.json()["param_hash"]
        
        # Train again (will overwrite)
        response2 = test_client.post(
            "/api/training/train/HASH_TEST?mode=5y&retain=none&archive=false"
        )
        assert response2.status_code == 200
        hash2 = response2.json()["param_hash"]
        
        # Hashes should match (same parameters)
        assert hash1 == hash2
        
        # Cleanup
        model_path = pathlib.Path(response2.json()["model_path"])
        if model_path.exists():
            model_path.unlink()

