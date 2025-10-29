"""
Feature Store for caching engineered features.

Provides fast access to pre-computed features with Redis caching.
"""
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import redis
from app.core.config import get_settings
from app.ml.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)
settings = get_settings()


class FeatureStore:
    """
    Feature store with Redis caching.
    
    Features:
    - Cache engineered features
    - TTL-based expiration
    - Batch feature retrieval
    - Feature versioning
    """
    
    def __init__(self, ttl: int = 3600, version: str = "v1"):
        """
        Initialize feature store.
        
        Args:
            ttl: Time-to-live for cached features in seconds (default: 1 hour)
            version: Feature version for cache keys
        """
        self.ttl = ttl
        self.version = version
        self.engineer = FeatureEngineer()
        
        # Connect to Redis
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        logger.info(f"Feature store initialized: version={version}, ttl={ttl}s")
    
    def _make_key(self, feature_type: str, identifier: str) -> str:
        """
        Make cache key.
        
        Args:
            feature_type: Type of feature (e.g., 'technical', 'sentiment')
            identifier: Unique identifier (e.g., symbol, signal_id)
            
        Returns:
            Cache key
        """
        return f"features:{self.version}:{feature_type}:{identifier}"
    
    def get_technical_features(
        self,
        symbol: str,
        period: str = "1mo",
        force_refresh: bool = False
    ) -> Dict[str, float]:
        """
        Get technical indicators for a symbol.
        
        Args:
            symbol: Stock symbol
            period: Time period for indicators
            force_refresh: Force refresh from source
            
        Returns:
            Dict of technical features
        """
        cache_key = self._make_key("technical", f"{symbol}:{period}")
        
        # Try cache first
        if not force_refresh:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached)
        
        # Compute features
        logger.debug(f"Cache miss: {cache_key}")
        features = self.engineer.add_technical_indicators(symbol, period)
        
        # Cache features
        self.redis_client.setex(
            cache_key,
            self.ttl,
            json.dumps(features)
        )
        
        return features
    
    def get_sentiment_features(
        self,
        sentiment: float,
        magnitude: float,
        credibility: float,
        force_refresh: bool = False
    ) -> Dict[str, float]:
        """
        Get sentiment aggregation features.
        
        Args:
            sentiment: Sentiment score
            magnitude: Magnitude score
            credibility: Credibility score
            force_refresh: Force refresh
            
        Returns:
            Dict of sentiment features
        """
        # Create identifier from inputs
        identifier = f"{sentiment:.2f}:{magnitude:.2f}:{credibility:.2f}"
        cache_key = self._make_key("sentiment", identifier)
        
        # Try cache first
        if not force_refresh:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached)
        
        # Compute features
        logger.debug(f"Cache miss: {cache_key}")
        features = self.engineer.add_sentiment_aggregation(
            sentiment, magnitude, credibility
        )
        
        # Cache features
        self.redis_client.setex(
            cache_key,
            self.ttl,
            json.dumps(features)
        )
        
        return features
    
    def get_temporal_features(
        self,
        timestamp: Optional[datetime] = None,
        force_refresh: bool = False
    ) -> Dict[str, float]:
        """
        Get temporal features.
        
        Args:
            timestamp: Timestamp to compute features for (None = now)
            force_refresh: Force refresh
            
        Returns:
            Dict of temporal features
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Create identifier from timestamp (rounded to hour)
        identifier = timestamp.strftime("%Y-%m-%d-%H")
        cache_key = self._make_key("temporal", identifier)
        
        # Try cache first
        if not force_refresh:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached)
        
        # Compute features
        logger.debug(f"Cache miss: {cache_key}")
        features = self.engineer.add_temporal_features(timestamp)
        
        # Cache features (longer TTL for temporal features)
        self.redis_client.setex(
            cache_key,
            self.ttl * 24,  # 24 hours
            json.dumps(features)
        )
        
        return features
    
    def get_interaction_features(
        self,
        base_features: Dict[str, float],
        force_refresh: bool = False
    ) -> Dict[str, float]:
        """
        Get interaction features.
        
        Args:
            base_features: Base features dict
            force_refresh: Force refresh
            
        Returns:
            Dict of interaction features
        """
        # Create identifier from base features
        identifier = ":".join([
            f"{k}={v:.2f}" for k, v in sorted(base_features.items())
        ])[:100]  # Limit length
        
        cache_key = self._make_key("interaction", identifier)
        
        # Try cache first
        if not force_refresh:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached)
        
        # Compute features
        logger.debug(f"Cache miss: {cache_key}")
        features = self.engineer.add_interaction_features(base_features)
        
        # Cache features
        self.redis_client.setex(
            cache_key,
            self.ttl,
            json.dumps(features)
        )
        
        return features
    
    def get_all_features(
        self,
        symbol: str,
        sentiment: float,
        magnitude: float,
        credibility: float,
        base_features: Optional[Dict[str, float]] = None,
        timestamp: Optional[datetime] = None,
        force_refresh: bool = False
    ) -> Dict[str, float]:
        """
        Get all engineered features.
        
        Args:
            symbol: Stock symbol
            sentiment: Sentiment score
            magnitude: Magnitude score
            credibility: Credibility score
            base_features: Base features for interactions
            timestamp: Timestamp for temporal features
            force_refresh: Force refresh all features
            
        Returns:
            Dict with all features
        """
        all_features = {}
        
        # Technical features
        technical = self.get_technical_features(symbol, force_refresh=force_refresh)
        all_features.update(technical)
        
        # Sentiment features
        sentiment_features = self.get_sentiment_features(
            sentiment, magnitude, credibility, force_refresh=force_refresh
        )
        all_features.update(sentiment_features)
        
        # Temporal features
        temporal = self.get_temporal_features(timestamp, force_refresh=force_refresh)
        all_features.update(temporal)
        
        # Interaction features
        if base_features:
            # Merge base features with computed features
            merged_features = {**base_features, **all_features}
            interaction = self.get_interaction_features(
                merged_features, force_refresh=force_refresh
            )
            all_features.update(interaction)
        
        return all_features
    
    def batch_get_technical_features(
        self,
        symbols: List[str],
        period: str = "1mo"
    ) -> Dict[str, Dict[str, float]]:
        """
        Get technical features for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            period: Time period
            
        Returns:
            Dict mapping symbol to features
        """
        results = {}
        
        for symbol in symbols:
            try:
                features = self.get_technical_features(symbol, period)
                results[symbol] = features
            except Exception as e:
                logger.error(f"Failed to get features for {symbol}: {e}")
                results[symbol] = {}
        
        return results
    
    def invalidate(self, feature_type: str, identifier: str):
        """
        Invalidate cached features.
        
        Args:
            feature_type: Type of feature
            identifier: Feature identifier
        """
        cache_key = self._make_key(feature_type, identifier)
        self.redis_client.delete(cache_key)
        logger.info(f"Invalidated cache: {cache_key}")
    
    def invalidate_all(self):
        """Invalidate all cached features."""
        pattern = f"features:{self.version}:*"
        keys = self.redis_client.keys(pattern)
        
        if keys:
            self.redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cached features")
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        pattern = f"features:{self.version}:*"
        keys = self.redis_client.keys(pattern)
        
        # Count by feature type
        type_counts = {}
        for key in keys:
            parts = key.split(":")
            if len(parts) >= 3:
                feature_type = parts[2]
                type_counts[feature_type] = type_counts.get(feature_type, 0) + 1
        
        return {
            'version': self.version,
            'total_keys': len(keys),
            'by_type': type_counts,
            'ttl': self.ttl
        }

