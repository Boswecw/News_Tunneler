"""Resilience patterns: retry logic, circuit breakers, graceful degradation."""
from functools import wraps
from typing import Callable, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from circuitbreaker import circuit
import httpx
from app.core.logging import logger


# Retry decorator for HTTP requests
def retry_on_http_error(max_attempts: int = 3, min_wait: int = 2, max_wait: int = 10):
    """
    Retry decorator for HTTP requests with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
    
    Usage:
        @retry_on_http_error(max_attempts=3)
        async def fetch_data(url: str):
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            httpx.HTTPError,
            httpx.TimeoutException,
            httpx.ConnectError,
            ConnectionError,
        )),
        before_sleep=before_sleep_log(logger, logger.level),
        reraise=True,
    )


# Retry decorator for general exceptions
def retry_on_exception(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator for general exceptions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exception types to retry on
    
    Usage:
        @retry_on_exception(max_attempts=3, exceptions=(ValueError, KeyError))
        def process_data(data):
            # Processing logic that might fail
            return result
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logger.level),
        reraise=True,
    )


# Circuit breaker for external API calls
def api_circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    """
    Circuit breaker decorator for external API calls.
    
    If `failure_threshold` consecutive failures occur, the circuit opens
    and all calls fail fast for `recovery_timeout` seconds.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
    
    Usage:
        @api_circuit_breaker(failure_threshold=5, recovery_timeout=60)
        def call_external_api(endpoint: str):
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
    """
    return circuit(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=Exception,
    )


# Combined retry + circuit breaker
def resilient_api_call(
    max_attempts: int = 3,
    min_wait: int = 2,
    max_wait: int = 10,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
):
    """
    Combined retry and circuit breaker decorator for resilient API calls.
    
    This provides both retry logic (for transient failures) and circuit breaking
    (for sustained failures).
    
    Usage:
        @resilient_api_call()
        async def fetch_stock_price(symbol: str):
            # API call logic
            return price
    """
    def decorator(func: Callable) -> Callable:
        # Apply circuit breaker first, then retry
        @api_circuit_breaker(failure_threshold, recovery_timeout)
        @retry_on_http_error(max_attempts, min_wait, max_wait)
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Graceful degradation wrapper
def with_fallback(fallback_value: Any = None, log_error: bool = True):
    """
    Graceful degradation decorator that returns fallback value on error.
    
    Args:
        fallback_value: Value to return if function fails
        log_error: Whether to log the error
    
    Usage:
        @with_fallback(fallback_value=0.0)
        def get_liquidity_score(ticker: str):
            # Might fail if API is down
            return api.get_volume(ticker)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.warning(
                        f"Function {func.__name__} failed: {e}. "
                        f"Returning fallback value: {fallback_value}"
                    )
                return fallback_value
        return wrapper
    return decorator


# Async version of retry decorator
def async_retry_on_http_error(max_attempts: int = 3, min_wait: int = 2, max_wait: int = 10):
    """
    Async retry decorator for HTTP requests with exponential backoff.
    
    Usage:
        @async_retry_on_http_error(max_attempts=3)
        async def fetch_data(url: str):
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            httpx.HTTPError,
            httpx.TimeoutException,
            httpx.ConnectError,
            ConnectionError,
        )),
        before_sleep=before_sleep_log(logger, logger.level),
        reraise=True,
    )


# Timeout wrapper
def with_timeout(seconds: int = 30):
    """
    Timeout decorator for functions.
    
    Args:
        seconds: Timeout in seconds
    
    Note: This is a simple wrapper. For production, consider using asyncio.wait_for
    for async functions or signal.alarm for sync functions.
    
    Usage:
        @with_timeout(seconds=10)
        def slow_operation():
            # Long-running operation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # For now, just execute the function
            # TODO: Implement actual timeout logic
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Helper function for safe API calls
async def safe_http_get(
    url: str,
    timeout: int = 10,
    max_attempts: int = 3,
) -> dict | None:
    """
    Safe HTTP GET with retry and error handling.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        max_attempts: Maximum retry attempts
    
    Returns:
        Response JSON or None if failed
    """
    @async_retry_on_http_error(max_attempts=max_attempts)
    async def _fetch():
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
    
    try:
        return await _fetch()
    except Exception as e:
        logger.error(f"Failed to fetch {url} after {max_attempts} attempts: {e}")
        return None

