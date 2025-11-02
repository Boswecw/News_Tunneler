"""Performance monitoring utilities."""
import time
import functools
from typing import Callable
from app.core.logging import logger


def timing_decorator(func: Callable) -> Callable:
    """
    Decorator to measure and log execution time of functions.
    
    Usage:
        @timing_decorator
        async def my_function():
            ...
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
            logger.info(
                f"⏱️  {func.__name__} completed in {elapsed:.2f}ms",
                extra={"function": func.__name__, "elapsed_ms": elapsed}
            )
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(
                f"⏱️  {func.__name__} failed after {elapsed:.2f}ms: {e}",
                extra={"function": func.__name__, "elapsed_ms": elapsed, "error": str(e)}
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
            logger.info(
                f"⏱️  {func.__name__} completed in {elapsed:.2f}ms",
                extra={"function": func.__name__, "elapsed_ms": elapsed}
            )
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(
                f"⏱️  {func.__name__} failed after {elapsed:.2f}ms: {e}",
                extra={"function": func.__name__, "elapsed_ms": elapsed, "error": str(e)}
            )
            raise
    
    # Return appropriate wrapper based on whether function is async
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class PerformanceMonitor:
    """
    Context manager for monitoring performance of code blocks.
    
    Usage:
        with PerformanceMonitor("database_query"):
            # ... code to monitor ...
            pass
    """
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        elapsed = (self.end_time - self.start_time) * 1000  # Convert to milliseconds
        
        if exc_type is None:
            logger.info(
                f"⏱️  {self.operation_name} completed in {elapsed:.2f}ms",
                extra={"operation": self.operation_name, "elapsed_ms": elapsed}
            )
        else:
            logger.error(
                f"⏱️  {self.operation_name} failed after {elapsed:.2f}ms: {exc_val}",
                extra={"operation": self.operation_name, "elapsed_ms": elapsed, "error": str(exc_val)}
            )
        
        return False  # Don't suppress exceptions

