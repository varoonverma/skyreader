"""
Logging configuration for the SkyReader TTY Message Parser.
"""
import logging
import sys
from typing import Dict, Any


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application logging.

    Args:
        log_level: The logging level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_formatter = logging.Formatter(log_format)

    # Get the root logger
    root_logger = logging.getLogger()

    # Clear any existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    # Set the log level
    level = getattr(logging, log_level.upper())
    root_logger.setLevel(level)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Suppress certain loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: The name of the logger

    Returns:
        Logger: A configured logger instance
    """
    return logging.getLogger(name)


def log_request_info(request_data: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Log information about a request.

    Args:
        request_data: The request data to log
        logger: The logger to use
    """
    # Sanitize the request data to remove sensitive information
    sanitized_data = {**request_data}

    # Truncate long messages for logging
    if "message" in sanitized_data and isinstance(sanitized_data["message"], str):
        if len(sanitized_data["message"]) > 100:
            sanitized_data["message"] = sanitized_data["message"][:100] + "..."

    logger.info(f"Processing request: {sanitized_data}")


def log_processing_result(message_id: str,
                          processing_time: float,
                          method: str,
                          success: bool,
                          logger: logging.Logger) -> None:
    """
    Log information about a processing result.

    Args:
        message_id: The ID of the processed message
        processing_time: The processing time in milliseconds
        method: The method used for processing (e.g., 'llm', 'antlr')
        success: Whether the processing was successful
        logger: The logger to use
    """
    status = "succeeded" if success else "failed"
    logger.info(
        f"Message {message_id} {status} in {processing_time:.2f}ms using {method}"
    )