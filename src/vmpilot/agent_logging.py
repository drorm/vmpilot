"""
Logging utilities for the VMPilot agent.
Provides structured logging functionality with enhanced metadata and formatting.
"""

import json
import logging
import traceback
from typing import Any, Dict, Union

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
    usage = response_metadata.get("usage", {})

    # if there's no usage data, return
    if not usage:
        return

    # Log token usage in single line format
    logging.getLogger(__name__).info(
        "TOKEN_USAGE: {'cache_creation_input_tokens': %d, 'cache_read_input_tokens': %d, 'input_tokens': %d, 'output_tokens': %d}",
        usage.get('cache_creation_input_tokens', 0),
        usage.get('cache_read_input_tokens', 0),
        usage.get('input_tokens', 0),
        usage.get('output_tokens', 0))


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
