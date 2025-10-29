"""
Request ID Middleware for request tracing.

Generates a unique ID for each request and adds it to logs and response headers.
"""
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.structured_logging import set_request_context, clear_request_context, get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates a unique request ID for each request.
    
    The request ID is:
    - Added to the response headers as 'X-Request-ID'
    - Added to all log messages via context variables
    - Available in the request state for use in endpoints
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and add request ID."""
        # Generate or extract request ID
        request_id = request.headers.get('X-Request-ID')
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in request state for access in endpoints
        request.state.request_id = request_id
        
        # Set context for logging
        set_request_context(request_id=request_id)
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'query_params': str(request.query_params),
                'client_host': request.client.host if request.client else None,
            }
        )
        
        try:
            # Process request
            response: Response = await call_next(request)
            
            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id
            
            # Log response
            logger.info(
                f"Response {response.status_code}",
                extra={
                    'status_code': response.status_code,
                    'method': request.method,
                    'path': request.url.path,
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Request failed: {str(e)}",
                exc_info=True,
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'error_type': type(e).__name__,
                }
            )
            raise
        
        finally:
            # Clear context after request
            clear_request_context()


def get_request_id(request: Request) -> str:
    """
    Get the request ID from the request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID string
    """
    return getattr(request.state, 'request_id', 'unknown')

