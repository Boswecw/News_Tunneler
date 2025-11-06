"""
Sentry Error Tracking Integration

Configures Sentry SDK for error tracking, performance monitoring, and alerting.
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

from app.core.config import get_settings
from app.core.logging import logger


def setup_sentry():
    """
    Initialize Sentry SDK with FastAPI, SQLAlchemy, Redis, and Celery integrations.

    Features:
    - Error tracking with stack traces
    - Performance monitoring (transaction traces)
    - Release tracking
    - Environment tagging
    - Custom context (user, tags, extras)
    - Breadcrumbs for debugging
    """
    settings = get_settings()

    # Skip if SENTRY_DSN not configured
    if not settings.sentry_dsn:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return

    # Determine environment and release
    environment = settings.env  # production, staging, development
    release = getattr(settings, 'app_version', None)  # e.g., "news-tunneler@1.0.0"

    # Initialize Sentry
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=environment,
        release=release,

        # Sample rate for error events (1.0 = 100% of errors)
        sample_rate=1.0,

        # Sample rate for performance monitoring (0.1 = 10% of transactions)
        # Reduce in production to avoid high volume
        traces_sample_rate=0.1 if environment == "production" else 1.0,

        # Enable performance profiling (captures function-level performance)
        profiles_sample_rate=0.1 if environment == "production" else 0.5,

        # Integrations
        integrations=[
            # FastAPI integration (automatic request tracing)
            FastApiIntegration(
                transaction_style="endpoint",  # Use endpoint names as transaction names
                failed_request_status_codes=[500, 501, 502, 503, 504, 505],
            ),

            # SQLAlchemy integration (query monitoring)
            SqlalchemyIntegration(),

            # Redis integration (cache monitoring)
            RedisIntegration(),

            # Celery integration (task monitoring)
            CeleryIntegration(
                monitor_beat_tasks=True,  # Monitor Celery Beat scheduled tasks
                exclude_beat_tasks=False,
            ),

            # Logging integration (capture logs as breadcrumbs)
            LoggingIntegration(
                level=logging.INFO,        # Breadcrumbs for INFO and above
                event_level=logging.ERROR  # Create Sentry events for ERROR and above
            ),
        ],

        # Send default PII (Personally Identifiable Information) to Sentry
        # Set to False in production if you have strict privacy requirements
        send_default_pii=False,

        # Attach stack traces to all messages (not just exceptions)
        attach_stacktrace=True,

        # Maximum breadcrumbs to keep (for debugging context)
        max_breadcrumbs=50,

        # Before send callback (filter/modify events before sending)
        before_send=before_send_callback,

        # Before breadcrumb callback (filter/modify breadcrumbs)
        before_breadcrumb=before_breadcrumb_callback,
    )

    logger.info(
        f"Sentry initialized: environment={environment}, "
        f"release={release}, traces_sample_rate={0.1 if environment == 'production' else 1.0}"
    )


def before_send_callback(event, hint):
    """
    Callback to filter or modify events before sending to Sentry.

    Use cases:
    - Filter out specific errors (e.g., known issues)
    - Scrub sensitive data
    - Add custom context
    - Skip events in certain conditions

    Args:
        event: Event dict to be sent to Sentry
        hint: Additional information about the event

    Returns:
        Modified event dict, or None to skip sending
    """
    # Example: Skip 404 errors (not actual application errors)
    if event.get("level") == "error":
        exception = hint.get("exc_info")
        if exception:
            exc_type, exc_value, exc_tb = exception
            # Add custom filtering logic here
            # if isinstance(exc_value, SpecificException):
            #     return None  # Don't send this error to Sentry

    # Example: Add custom context
    event.setdefault("tags", {})
    event["tags"]["backend"] = "fastapi"

    return event


def before_breadcrumb_callback(crumb, hint):
    """
    Callback to filter or modify breadcrumbs before adding to context.

    Breadcrumbs provide debugging context (logs, HTTP requests, DB queries, etc.)

    Args:
        crumb: Breadcrumb dict
        hint: Additional information

    Returns:
        Modified breadcrumb dict, or None to skip
    """
    # Example: Filter out noisy breadcrumbs
    if crumb.get("category") == "query":
        # Skip very common queries to reduce noise
        query = crumb.get("data", {}).get("query", "")
        if "SELECT 1" in query:  # Health check queries
            return None

    return crumb


def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture a custom message to Sentry.

    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **kwargs: Additional context (tags, extras, user)

    Example:
        capture_message(
            "User completed onboarding",
            level="info",
            tags={"user_type": "premium"},
            extras={"step": "final"}
        )
    """
    with sentry_sdk.push_scope() as scope:
        # Add tags
        if "tags" in kwargs:
            for key, value in kwargs["tags"].items():
                scope.set_tag(key, value)

        # Add extra context
        if "extras" in kwargs:
            for key, value in kwargs["extras"].items():
                scope.set_extra(key, value)

        # Add user context
        if "user" in kwargs:
            scope.set_user(kwargs["user"])

        sentry_sdk.capture_message(message, level=level)


def capture_exception(exception: Exception, **kwargs):
    """
    Capture an exception to Sentry with additional context.

    Args:
        exception: Exception to capture
        **kwargs: Additional context (tags, extras, user)

    Example:
        try:
            risky_operation()
        except Exception as e:
            capture_exception(
                e,
                tags={"operation": "data_sync"},
                extras={"ticker": "AAPL"}
            )
    """
    with sentry_sdk.push_scope() as scope:
        # Add tags
        if "tags" in kwargs:
            for key, value in kwargs["tags"].items():
                scope.set_tag(key, value)

        # Add extra context
        if "extras" in kwargs:
            for key, value in kwargs["extras"].items():
                scope.set_extra(key, value)

        # Add user context
        if "user" in kwargs:
            scope.set_user(kwargs["user"])

        sentry_sdk.capture_exception(exception)


def set_user_context(user_id: str, email: str = None, username: str = None):
    """
    Set user context for all subsequent Sentry events.

    Args:
        user_id: User ID
        email: User email (optional)
        username: Username (optional)

    Example:
        set_user_context(
            user_id="12345",
            email="user@example.com",
            username="john_doe"
        )
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username
    })


def set_context(key: str, value: dict):
    """
    Set custom context for debugging.

    Args:
        key: Context key (e.g., "database", "api_call")
        value: Context data (dict)

    Example:
        set_context("article_processing", {
            "article_id": "123",
            "source": "bloomberg",
            "symbols": ["AAPL", "MSFT"]
        })
    """
    sentry_sdk.set_context(key, value)


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: dict = None):
    """
    Manually add a breadcrumb for debugging context.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "http", "database", "cache")
        level: Severity level
        data: Additional data

    Example:
        add_breadcrumb(
            message="Fetched article from API",
            category="api",
            level="info",
            data={"article_id": "123", "latency_ms": 45}
        )
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


# Convenience decorator for automatic error capture
def sentry_trace(func):
    """
    Decorator to automatically trace function execution in Sentry.

    Captures function arguments, return values, and exceptions.

    Example:
        @sentry_trace
        def process_article(article_id: str):
            # Your code here
            pass
    """
    import functools

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        with sentry_sdk.start_transaction(op="function", name=func.__name__):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                capture_exception(
                    e,
                    extras={
                        "function": func.__name__,
                        "args": str(args)[:200],  # Truncate to avoid large payloads
                        "kwargs": str(kwargs)[:200]
                    }
                )
                raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        with sentry_sdk.start_transaction(op="function", name=func.__name__):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                capture_exception(
                    e,
                    extras={
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }
                )
                raise

    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
