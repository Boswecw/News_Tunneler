"""Rate limiting middleware for API endpoints."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from app.core.logging import logger

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default limit for all endpoints
    storage_uri="memory://",  # Use in-memory storage (can be changed to Redis)
)

# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded errors."""
    logger.warning(
        f"Rate limit exceeded for {get_remote_address(request)} "
        f"on {request.url.path}"
    )
    
    return Response(
        content='{"detail": "Rate limit exceeded. Please try again later."}',
        status_code=429,
        headers={
            "Content-Type": "application/json",
            "Retry-After": str(exc.detail.split("Retry after ")[1].split(" ")[0] if "Retry after" in exc.detail else "60"),
        },
    )


# Rate limit decorators for different endpoint types
def rate_limit_signals(func):
    """Rate limit for ML signal endpoints (10 requests/minute)."""
    return limiter.limit("10/minute")(func)


def rate_limit_articles(func):
    """Rate limit for article endpoints (30 requests/minute)."""
    return limiter.limit("30/minute")(func)


def rate_limit_stream(func):
    """Rate limit for streaming endpoints (5 requests/minute)."""
    return limiter.limit("5/minute")(func)


def rate_limit_admin(func):
    """Rate limit for admin endpoints (5 requests/hour)."""
    return limiter.limit("5/hour")(func)


def rate_limit_analysis(func):
    """Rate limit for analysis endpoints (20 requests/minute)."""
    return limiter.limit("20/minute")(func)

