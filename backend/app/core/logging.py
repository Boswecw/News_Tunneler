"""Logging configuration."""
import logging
import sys
from .config import get_settings

settings = get_settings()


def setup_logging():
    """Configure logging for the application."""
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    return root_logger


logger = setup_logging()

