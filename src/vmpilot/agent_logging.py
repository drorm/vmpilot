"""
Logging utilities for the VMPilot agent.
Provides structured logging functionality with enhanced metadata and formatting.
"""

import logging
import json
import traceback
from typing import Any

# Configure logging with enhanced format for debugging and analysis
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s\n",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create and configure the logger
logger = logging.getLogger(__name__)


def log_message(category: str, message: Any, level: str = "info"):
    """Structured logging helper for consistent formatting with enhanced metadata

    Args:
        category: The logging category/component
        message: The message to log (can be any type)
        level: Logging level (debug, info, warning, error)
    """
    log_func = getattr(logger, level)
    try:
        if isinstance(message, (dict, list)):
            # Convert non-serializable objects to strings in dictionaries
            def serialize_value(v):
                try:
                    json.dumps(v)
                    return v
                except (TypeError, ValueError):
                    return str(v)

            if isinstance(message, dict):
                serializable_message = {
                    k: serialize_value(v) for k, v in message.items()
                }
            else:  # list
                serializable_message = [serialize_value(v) for v in message]
            msg_content = json.dumps(serializable_message, indent=2)
        else:
            msg_content = str(message)

        formatted_msg = f"{category}: {msg_content}"
        log_func(formatted_msg)
    except Exception as e:
        log_func(f"{category}: Error formatting message: {str(e)}")


def log_error(category: str, error: Exception, phase: str):
    """Helper function to log errors with stack traces

    Args:
        category: The logging category/component
        error: The exception object
        phase: The phase/operation where the error occurred
    """
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
