"""Prompt caching functionality for VMPilot."""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def inject_prompt_caching(messages: List[Dict[str, Any]]) -> None:
    """
    Set cache breakpoints for the 3 most recent turns.
    One cache breakpoint is left for tools/system prompt, to be shared across sessions.
    See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
    Adapted from https://github.com/anthropics/anthropic-quickstarts/blob/main/computer-use-demo/computer_use_demo/loop.py
    """
    breakpoints_remaining = 3

    for message in reversed(messages):
        if isinstance(message.get("content"), list):
            content = message["content"]
            if not content:
                continue
            logger.info(f"Looking at message: {content[0]['text'][:60]}")

            # For user messages or assistant messages with tool results
            if message["role"] == "user" or (
                message["role"] == "assistant"
                and any("tool_calls" in item for item in content)
            ):
                if breakpoints_remaining > 0:
                    # show the first 60 characters of this message
                    logger.info(
                        f"Adding cache control to message: {content[0]['text'][:60]}"
                    )
                    breakpoints_remaining -= 1
                    # Add cache control to the last content item
                    content[-1]["cache_control"] = {"type": "ephemeral"}
                else:
                    # Explicitly remove cache control from older messages
                    content[-1].pop("cache_control", None)
                    # We only need to remove one extra turn's cache control
                    break


def add_cache_control(content: Dict[str, Any]) -> Dict[str, Any]:
    """Add cache control to content."""
    if "cache_control" not in content:
        content["cache_control"] = {"type": "ephemeral"}
    return content


def create_ephemeral_system_prompt(
    base_prompt: str, suffix: Optional[str] = None
) -> Dict[str, Any]:
    """Create a system prompt with cache control."""
    text = base_prompt
    if suffix:
        text = f"{text}\n\n{suffix}"

    return {"text": text, "cache_control": {"type": "ephemeral"}}
