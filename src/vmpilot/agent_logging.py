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


def _serialize_message(message: Union[Dict[Any, Any], list[Any], Any]) -> str:
    """Serialize message to JSON string, converting non-serializable objects to strings."""
    if not isinstance(message, (dict, list)):
        return str(message)

    def serialize_value(v: Any) -> Any:
        try:
            json.dumps(v)
            return v
        except (TypeError, ValueError):
            return str(v)

    # Prepare serializable message based on type
    serializable_message: Union[Dict[Any, Any], list[Any]]

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
        usage.get("cache_creation_input_tokens", 0),
        usage.get("cache_read_input_tokens", 0),
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
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


def log_conversation_messages(messages: list[Any], level: str = "info") -> None:
    """
    Log the full conversation history in a structured, readable format.

    This function provides a clean view of all messages in the conversation,
    showing each message's type, content, and relevant metadata in a format
    that's easy to read and analyze.

    Args:
        messages: List of message objects in the conversation
        level: Logging level (default: info)
    """
    log_func = getattr(logger, level)

    try:
        # Create a structured representation of the conversation
        conversation_log = []

        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__

            # Extract content in a readable format
            if isinstance(msg.content, list):
                content_repr = []
                for item in msg.content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            content_repr.append(f"TEXT: {item.get('text', '')}")
                        elif item.get("type") == "tool_use":
                            content_repr.append(
                                f"TOOL_USE: {item.get('name', '')} - "
                                f"Input: {json.dumps(item.get('input', {}))}"
                            )
                        else:
                            content_repr.append(f"OTHER: {str(item)}")
                    else:
                        content_repr.append(str(item))
                content = "\n  - " + "\n  - ".join(content_repr)
            else:
                # Truncate very long content for readability
                content = str(msg.content)
                # if len(content) > 500:
                # content = content[:500] + "... [truncated]"

            # Get relevant metadata
            metadata = {}
            if hasattr(msg, "id") and msg.id:
                metadata["id"] = msg.id
            if hasattr(msg, "name") and msg.name:
                metadata["name"] = msg.name
            if hasattr(msg, "tool_call_id") and msg.tool_call_id:
                metadata["tool_call_id"] = msg.tool_call_id

            # Add usage information if available
            usage_info = ""
            if hasattr(msg, "response_metadata") and msg.response_metadata:
                usage = msg.response_metadata.get("usage", {})
                if usage:
                    usage_info = (
                        f" [Tokens: in={usage.get('input_tokens', 0)}, "
                        f"out={usage.get('output_tokens', 0)}]"
                    )

            # Format the message entry
            msg_entry = f"[{i+1}] {msg_type}{usage_info}"
            if metadata:
                msg_entry += f" {metadata}"
            msg_entry += f":\n{content}"

            conversation_log.append(msg_entry)

        # Log the structured conversation
        log_func(f"CONVERSATION HISTORY:\n" + "\n\n".join(conversation_log))

    except Exception as e:
        log_func(f"Error logging conversation: {str(e)}")
        log_func(traceback.format_exc())
