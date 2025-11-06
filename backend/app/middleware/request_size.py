"""Request size limiting middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from typing import Callable
from app.core.logging import logger


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size to prevent DoS attacks.

    Rejects requests with bodies larger than the configured maximum size.
    """

    def __init__(self, app, max_size: int = 10_000_000):  # 10 MB default
        """
        Initialize the middleware.

        Args:
            app: FastAPI application
            max_size: Maximum request body size in bytes (default: 10MB)
        """
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and check body size.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response (or 413 if body too large)
        """
        # Check Content-Length header
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                content_length_int = int(content_length)

                if content_length_int > self.max_size:
                    logger.warning(
                        f"Request body too large: {content_length_int} bytes (max: {self.max_size})",
                        extra={
                            "client_ip": request.client.host if request.client else "unknown",
                            "path": request.url.path,
                            "method": request.method,
                            "content_length": content_length_int
                        }
                    )

                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request body too large. Maximum size is {self.max_size // 1_000_000}MB."
                        }
                    )
            except ValueError:
                # Invalid Content-Length header
                logger.warning(
                    f"Invalid Content-Length header: {content_length}",
                    extra={
                        "client_ip": request.client.host if request.client else "unknown",
                        "path": request.url.path
                    }
                )
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header"}
                )

        # Process request normally
        response = await call_next(request)
        return response


def setup_request_size_limit(app, max_size: int = 10_000_000):
    """
    Add request size limiting middleware to FastAPI app.

    Args:
        app: FastAPI application
        max_size: Maximum request body size in bytes (default: 10MB)
    """
    app.add_middleware(RequestSizeLimitMiddleware, max_size=max_size)
    logger.info(f"Request size limit middleware enabled: {max_size // 1_000_000}MB max")
