"""
Model Registry Service

Manages trained model metadata, parameter hashing, and version tracking.
Provides a single source of truth for all trained price prediction models.
"""
import json
import hashlib
import pathlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import sys
import sklearn
import pandas as pd
import numpy as np
import yfinance


@dataclass
class ModelMetadata:
    """Metadata for a trained model."""
    ticker: str
    mode: str  # "5y" or "10y"
    param_hash: str
    r2_score: float
    n_observations: int
    trained_at: str  # ISO8601 timestamp
    model_path: str
    python_version: str
    sklearn_version: str
    pandas_version: str
    numpy_version: str
    yfinance_version: str
    date_range_start: str
    date_range_end: str
    indicator_config: Dict[str, Any]
    archive_path: Optional[str] = None


class ModelRegistry:
    """Manages the registry of trained models."""
    
    def __init__(self, registry_path: pathlib.Path):
        """
        Initialize the model registry.
        
        Args:
            registry_path: Path to registry.json file
        """
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
    def load(self) -> Dict[str, ModelMetadata]:
        """
        Load the registry from disk.
        
        Returns:
            Dictionary mapping model keys (ticker_mode) to metadata
        """
        if not self.registry_path.exists():
            return {}
        
        with open(self.registry_path, 'r') as f:
            data = json.load(f)
        
        # Convert dict entries back to ModelMetadata objects
        registry = {}
        for key, value in data.items():
            registry[key] = ModelMetadata(**value)
        
        return registry
    
    def save(self, registry: Dict[str, ModelMetadata]) -> None:
        """
        Save the registry to disk.
        
        Args:
            registry: Dictionary mapping model keys to metadata
        """
        # Convert ModelMetadata objects to dicts
        data = {key: asdict(metadata) for key, metadata in registry.items()}
        
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_model(
        self,
        ticker: str,
        mode: str,
        model_path: str,
        r2_score: float,
        n_observations: int,
        date_range_start: str,
        date_range_end: str,
        indicator_config: Dict[str, Any],
        archive_path: Optional[str] = None
    ) -> ModelMetadata:
        """
        Add or update a model in the registry.
        
        Args:
            ticker: Stock ticker symbol
            mode: Training mode ("5y" or "10y")
            model_path: Path to saved model file
            r2_score: R² score from training
            n_observations: Number of training observations
            date_range_start: Start date of training data (ISO8601)
            date_range_end: End date of training data (ISO8601)
            indicator_config: Configuration dict for technical indicators
            archive_path: Optional path to archived training data
            
        Returns:
            ModelMetadata object for the added model
        """
        # Compute parameter hash for reproducibility
        param_hash = self.compute_param_hash(
            ticker=ticker,
            mode=mode,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            indicator_config=indicator_config
        )
        
        # Create metadata
        metadata = ModelMetadata(
            ticker=ticker,
            mode=mode,
            param_hash=param_hash,
            r2_score=r2_score,
            n_observations=n_observations,
            trained_at=datetime.now(timezone.utc).isoformat() + "Z",
            model_path=model_path,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            sklearn_version=sklearn.__version__,
            pandas_version=pd.__version__,
            numpy_version=np.__version__,
            yfinance_version=yfinance.__version__,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            indicator_config=indicator_config,
            archive_path=archive_path
        )
        
        # Load existing registry
        registry = self.load()
        
        # Add/update model
        key = f"{ticker}_{mode}"
        registry[key] = metadata
        
        # Save registry
        self.save(registry)
        
        return metadata
    
    def get_model(self, ticker: str, mode: str) -> Optional[ModelMetadata]:
        """
        Get metadata for a specific model.
        
        Args:
            ticker: Stock ticker symbol
            mode: Training mode ("5y" or "10y")
            
        Returns:
            ModelMetadata if found, None otherwise
        """
        registry = self.load()
        key = f"{ticker}_{mode}"
        return registry.get(key)
    
    def list_models(self) -> List[ModelMetadata]:
        """
        List all models in the registry.
        
        Returns:
            List of ModelMetadata objects
        """
        registry = self.load()
        return list(registry.values())
    
    def remove_model(self, ticker: str, mode: str) -> bool:
        """
        Remove a model from the registry.
        
        Args:
            ticker: Stock ticker symbol
            mode: Training mode ("5y" or "10y")
            
        Returns:
            True if model was removed, False if not found
        """
        registry = self.load()
        key = f"{ticker}_{mode}"
        
        if key in registry:
            del registry[key]
            self.save(registry)
            return True
        
        return False
    
    @staticmethod
    def compute_param_hash(
        ticker: str,
        mode: str,
        date_range_start: str,
        date_range_end: str,
        indicator_config: Dict[str, Any]
    ) -> str:
        """
        Compute deterministic hash of training parameters.
        
        Args:
            ticker: Stock ticker symbol
            mode: Training mode
            date_range_start: Start date
            date_range_end: End date
            indicator_config: Indicator configuration
            
        Returns:
            SHA256 hash of parameters
        """
        # Create deterministic string representation
        params = {
            "ticker": ticker,
            "mode": mode,
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
            "indicator_config": indicator_config
        }
        
        # Sort keys for determinism
        param_str = json.dumps(params, sort_keys=True)
        
        # Compute hash
        return hashlib.sha256(param_str.encode()).hexdigest()[:16]

