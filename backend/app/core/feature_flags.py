"""
Feature Flag Management System

Provides database-backed feature flags for enabling/disabling features without code changes.
Supports A/B testing and gradual rollout.
"""
from enum import Enum
from typing import Dict, Optional
from app.core.structured_logging import get_logger

logger = get_logger(__name__)


class FeatureFlag(str, Enum):
    """Available feature flags."""
    # Core Features
    LLM_ANALYSIS = "llm_analysis"
    ML_PREDICTIONS = "ml_predictions"
    
    # Data Sources
    RSS_POLLING = "rss_polling"
    SOCIAL_SENTIMENT = "social_sentiment"
    TWITTER_INTEGRATION = "twitter_integration"
    REDDIT_INTEGRATION = "reddit_integration"
    INSIDER_TRADING = "insider_trading"
    
    # Notifications
    EMAIL_DIGESTS = "email_digests"
    SLACK_ALERTS = "slack_alerts"
    WEBHOOK_NOTIFICATIONS = "webhook_notifications"
    
    # Advanced Features
    ADVANCED_ML = "advanced_ml"
    TIME_SERIES_FORECASTING = "time_series_forecasting"
    FINBERT_SENTIMENT = "finbert_sentiment"
    
    # Infrastructure
    CELERY_TASKS = "celery_tasks"
    REDIS_CACHING = "redis_caching"
    RATE_LIMITING = "rate_limiting"
    
    # Experimental
    WEBSOCKET_V2 = "websocket_v2"
    GRAPHQL_API = "graphql_api"


class FeatureFlagManager:
    """
    Manage feature flags with in-memory caching.
    
    Flags are stored in-memory with default values. In production, these would
    be stored in a database or configuration service (e.g., LaunchDarkly).
    """
    
    def __init__(self):
        """Initialize feature flag manager with default values."""
        self._flags: Dict[str, bool] = {
            # Core Features - Enabled by default
            FeatureFlag.LLM_ANALYSIS: True,
            FeatureFlag.ML_PREDICTIONS: True,
            FeatureFlag.RSS_POLLING: True,
            
            # Data Sources - Disabled by default (not implemented yet)
            FeatureFlag.SOCIAL_SENTIMENT: False,
            FeatureFlag.TWITTER_INTEGRATION: False,
            FeatureFlag.REDDIT_INTEGRATION: False,
            FeatureFlag.INSIDER_TRADING: False,
            
            # Notifications - Enabled by default
            FeatureFlag.EMAIL_DIGESTS: True,
            FeatureFlag.SLACK_ALERTS: True,
            FeatureFlag.WEBHOOK_NOTIFICATIONS: False,
            
            # Advanced Features - Disabled by default (Phase 3)
            FeatureFlag.ADVANCED_ML: False,
            FeatureFlag.TIME_SERIES_FORECASTING: False,
            FeatureFlag.FINBERT_SENTIMENT: False,
            
            # Infrastructure - Enabled (Phase 1 & 2)
            FeatureFlag.CELERY_TASKS: False,  # Will enable when Celery is ready
            FeatureFlag.REDIS_CACHING: True,
            FeatureFlag.RATE_LIMITING: True,
            
            # Experimental - Disabled by default
            FeatureFlag.WEBSOCKET_V2: False,
            FeatureFlag.GRAPHQL_API: False,
        }
        
        logger.info("Feature flag manager initialized", extra={
            'enabled_flags': [k for k, v in self._flags.items() if v],
            'total_flags': len(self._flags)
        })
    
    def is_enabled(self, flag: FeatureFlag) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag: Feature flag to check
            
        Returns:
            True if enabled, False otherwise
        """
        enabled = self._flags.get(flag.value, False)
        logger.debug(f"Feature flag check: {flag.value} = {enabled}")
        return enabled
    
    def enable(self, flag: FeatureFlag) -> None:
        """
        Enable a feature flag.
        
        Args:
            flag: Feature flag to enable
        """
        self._flags[flag.value] = True
        logger.info(f"Feature flag enabled: {flag.value}")
    
    def disable(self, flag: FeatureFlag) -> None:
        """
        Disable a feature flag.
        
        Args:
            flag: Feature flag to disable
        """
        self._flags[flag.value] = False
        logger.info(f"Feature flag disabled: {flag.value}")
    
    def toggle(self, flag: FeatureFlag) -> bool:
        """
        Toggle a feature flag.
        
        Args:
            flag: Feature flag to toggle
            
        Returns:
            New state of the flag
        """
        new_state = not self._flags.get(flag.value, False)
        self._flags[flag.value] = new_state
        logger.info(f"Feature flag toggled: {flag.value} = {new_state}")
        return new_state
    
    def get_all(self) -> Dict[str, bool]:
        """
        Get all feature flags and their states.
        
        Returns:
            Dictionary of flag names to boolean states
        """
        return self._flags.copy()
    
    def set_flag(self, flag_name: str, enabled: bool) -> None:
        """
        Set a feature flag by name.
        
        Args:
            flag_name: Name of the flag
            enabled: Whether to enable or disable
        """
        if flag_name in [f.value for f in FeatureFlag]:
            self._flags[flag_name] = enabled
            logger.info(f"Feature flag set: {flag_name} = {enabled}")
        else:
            logger.warning(f"Unknown feature flag: {flag_name}")


# Global feature flag manager instance
_feature_flags: Optional[FeatureFlagManager] = None


def get_feature_flags() -> FeatureFlagManager:
    """
    Get the global feature flag manager instance.
    
    Returns:
        FeatureFlagManager instance
    """
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlagManager()
    return _feature_flags


def is_feature_enabled(flag: FeatureFlag) -> bool:
    """
    Check if a feature is enabled (convenience function).
    
    Args:
        flag: Feature flag to check
        
    Returns:
        True if enabled, False otherwise
    """
    return get_feature_flags().is_enabled(flag)


# Decorator for feature-gated endpoints
def require_feature(flag: FeatureFlag):
    """
    Decorator to require a feature flag for an endpoint.
    
    Usage:
        @router.get("/experimental")
        @require_feature(FeatureFlag.WEBSOCKET_V2)
        def experimental_endpoint():
            return {"status": "ok"}
    """
    def decorator(func):
        from functools import wraps
        from fastapi import HTTPException
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not is_feature_enabled(flag):
                logger.warning(f"Feature disabled: {flag.value}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Feature '{flag.value}' is currently disabled"
                )
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not is_feature_enabled(flag):
                logger.warning(f"Feature disabled: {flag.value}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Feature '{flag.value}' is currently disabled"
                )
            return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Example usage:
if __name__ == "__main__":
    # Get feature flags
    flags = get_feature_flags()
    
    # Check flags
    print(f"LLM Analysis enabled: {flags.is_enabled(FeatureFlag.LLM_ANALYSIS)}")
    print(f"Twitter enabled: {flags.is_enabled(FeatureFlag.TWITTER_INTEGRATION)}")
    
    # Toggle flag
    flags.toggle(FeatureFlag.TWITTER_INTEGRATION)
    print(f"Twitter enabled after toggle: {flags.is_enabled(FeatureFlag.TWITTER_INTEGRATION)}")
    
    # Get all flags
    print("\nAll flags:")
    for flag_name, enabled in flags.get_all().items():
        print(f"  {flag_name}: {enabled}")

