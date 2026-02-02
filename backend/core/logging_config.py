"""
Logging configuration for Word Wiz AI backend.

Provides centralized logging setup with structured output for production.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_format: Optional[str] = None,
    enable_performance_logging: bool = False
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Custom log format string. If None, uses default format.
        enable_performance_logging: Whether to enable detailed performance logs.
    """
    if log_format is None:
        # Use structured format for production, human-readable for development
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set third-party library log levels to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    # Performance logging configuration
    if enable_performance_logging:
        logging.getLogger("performance").setLevel(logging.DEBUG)
    else:
        logging.getLogger("performance").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Name of the module (typically __name__).

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)
