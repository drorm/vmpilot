"""
Logging utilities for the VMPilot agent.
Provides structured logging functionality with enhanced metadata and formatting.
"""

import json
import logging
import traceback
from typing import Any, Dict, Union, Optional

# Global logger instances
logger = None
ALL_LOGGERS = []  # Keep track of all loggers


def setup_logging(level: str = "INFO") -> None:
    """
    Setup global logging configuration with the specified level.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global logger

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Update all registered loggers
    for logger in ALL_LOGGERS:
        logger.setLevel(numeric_level)

    logger = logging.getLogger("vmpilot")
    logger.setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the specified name.
    The logger will be tracked for global level management.

    Args:
        name: Name for the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    if logger not in ALL_LOGGERS:
        ALL_LOGGERS.append(logger)
    return logger


# Configure logging with enhanced format for debugging and analysis
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s\n",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def _serialize_message(message: Union[Dict, list, Any]) -> str:
    """Serialize message to JSON string, converting non-serializable objects to strings."""
    if not isinstance(message, (dict, list)):
        return str(message)

    def serialize_value(v):
        try:
            json.dumps(v)
            return v
        except (TypeError, ValueError):
            return str(v)

    if isinstance(message, dict):
        serializable_message = {k: serialize_value(v) for k, v in message.items()}
    else:  # list
        serializable_message = [serialize_value(v) for v in message]

    return json.dumps(serializable_message, indent=2)


def log_message(category: str, message: Any, level: str = "debug") -> None:
    """Log a message with consistent formatting."""
    log_func = getattr(logger, level)
    try:
        msg_content = _serialize_message(message)
        log_func(f"{category}: {msg_content}")
    except Exception as e:
        log_func(f"{category}: Error formatting message: {str(e)}")


def log_error(category: str, error: Exception, phase: str) -> None:
    """Log an error with stack trace."""
    log_message(
        category,
        {
            "phase": phase,
            "error": str(error),
            "stack_trace": (
                "".join(traceback.format_tb(error.__traceback__))
                if error.__traceback__
                else None
            ),
        },
        "error",
    )


def log_message_processing(role: str, content_type: str, level: str = "debug") -> None:
    """Log when a message is being processed"""
    log_message(
        "MESSAGE_PROCESSING", {"role": role, "content_type": content_type}, level
    )


def log_message_content(message: Any, content: Any, level: str = "debug") -> None:
    """Log detailed message content information"""
    log_message(
        "MESSAGE_CONTENT",
        {
            "type": type(message).__name__,
            "content_type": type(content).__name__,
            "length": len(str(content)),
            "additional_kwargs": getattr(message, "additional_kwargs", {}),
            "response_metadata": getattr(message, "response_metadata", {}),
            "tool_calls": getattr(message, "tool_calls", []),
            "usage_metadata": getattr(message, "usage_metadata", {}),
            "raw_content": str(content),
        },
        level,
    )


def log_token_usage(message: Any, level: str = "debug") -> None:
    """Log token usage and related metadata"""
    response_metadata = getattr(message, "response_metadata", {})
    usage_metadata = getattr(message, "usage_metadata", {})
    tool_calls = getattr(message, "tool_calls", [])

    log_message(
        "TOKEN_USAGE",
        {
            "usage": response_metadata.get("usage", {}),
            "tool_calls": [
                {
                    "name": tool["name"],
                    "args": tool["args"],
                    "type": tool["type"],
                }
                for tool in tool_calls
            ],
            "usage_metadata": usage_metadata,
        },
        level,
    )


def log_tool_message(message: Any, level: str = "debug") -> None:
    """Log when a tool message is received"""
    log_message("TOOL_MESSAGE_RECEIVED", str(message), "debug")


def log_message_received(message: Any, level: str = "debug") -> None:
    """Log when any message is received"""
    log_message(
        "MESSAGE_RECEIVED",
        {
            type(message).__name__: str(message),
        },
        level,
    )
