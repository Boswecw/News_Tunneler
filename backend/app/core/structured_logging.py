"""
Structured Logging with JSON formatting and request tracing.

Provides JSON-formatted logs with contextual information for better observability.
"""
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger

# Context variable for request ID tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds contextual information to log records.
    
    Adds:
    - timestamp (ISO 8601)
    - request_id (from context)
    - user_id (from context)
    - service name
    - environment
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO 8601 format
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat() + 'Z'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_record['request_id'] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_record['user_id'] = user_id
        
        # Add service information
        log_record['service'] = 'news-tunneler-backend'
        
        # Add file and line information for debugging
        log_record['file'] = record.filename
        log_record['line'] = record.lineno
        log_record['function'] = record.funcName
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def setup_structured_logging(log_level: str = "INFO", log_file: str = "logs/app.log") -> None:
    """
    Configure structured logging with JSON formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file for persistent logs
    """
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(logger)s %(message)s',
        timestamp=True
    )
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    # Separate file handler for errors only
    error_handler = logging.FileHandler('logs/errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    logger.addHandler(error_handler)
    
    # Configure third-party loggers to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    logger.info("Structured logging initialized", extra={
        'log_level': log_level,
        'log_file': log_file
    })


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_request_context(request_id: str, user_id: str = '') -> None:
    """
    Set request context for logging.
    
    Args:
        request_id: Unique request identifier
        user_id: User identifier (optional)
    """
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context() -> None:
    """Clear request context after request completion."""
    request_id_var.set('')
    user_id_var.set('')


def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs) -> None:
    """
    Log a message with additional context.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional context to include in log
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra=kwargs)


# Example usage:
if __name__ == "__main__":
    # Setup logging
    setup_structured_logging(log_level="DEBUG")
    
    # Get logger
    logger = get_logger(__name__)
    
    # Set request context
    set_request_context(request_id="req-123", user_id="user-456")
    
    # Log messages
    logger.info("Processing request", extra={'endpoint': '/api/signals/top', 'method': 'GET'})
    logger.debug("Cache hit", extra={'key': 'liquidity:AAPL', 'ttl': 3600})
    logger.warning("Rate limit approaching", extra={'current': 9, 'limit': 10})
    
    try:
        raise ValueError("Example error")
    except Exception as e:
        logger.error("Error occurred", exc_info=True, extra={'error_type': type(e).__name__})
    
    # Clear context
    clear_request_context()
    
    logger.info("Request completed")

