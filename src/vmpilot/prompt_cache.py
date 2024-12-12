"""Prompt caching functionality for VMPilot."""

from typing import Any, Dict, List, Optional


def inject_prompt_caching(messages: List[Dict[str, Any]]) -> None:
    """
    Enhanced caching strategy that:
    1. Sets cache breakpoints for the 3 most recent message turns
    2. Preserves cache state for system prompts
    3. Handles tool outputs appropriately
    4. Maintains cache continuity across sessions

    Args:
        messages: List of message dictionaries containing role and content
    """
    # We reserve 3 cache breakpoints for recent history, 1 for system
    breakpoints_remaining = 3

    # Process messages in reverse to handle most recent first
    for message in reversed(messages):
        role = message["role"]
        content = message.get("content", [])

        # Skip if no content or not in correct format
        if not isinstance(content, list):
            continue

        if role == "user":
            # Handle user messages
            if breakpoints_remaining > 0 and content:
                breakpoints_remaining -= 1
                # Add cache control to the last content item
                content[-1]["cache_control"] = {"type": "ephemeral"}
            elif breakpoints_remaining <= 0 and content:
                # Remove cache control if present
                if "cache_control" in content[-1]:
                    del content[-1]["cache_control"]

        elif role == "assistant":
            # Handle assistant messages including tool outputs
            if breakpoints_remaining > 0 and content:
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            # Text responses share cache breakpoint with preceding user message
                            item["cache_control"] = {"type": "ephemeral"}
                        elif item.get("type") == "tool_use":
                            # Tool uses are always ephemeral but don't consume breakpoints
                            item["cache_control"] = {"type": "ephemeral"}


def add_cache_control(content: Dict[str, Any]) -> Dict[str, Any]:
    """Add cache control to content."""
    if "cache_control" not in content:
        content["cache_control"] = {"type": "ephemeral"}
    return content


def create_ephemeral_system_prompt(
    base_prompt: str, suffix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a system prompt with appropriate cache control.
    The base prompt is marked as persistent since it rarely changes,
    while any dynamic suffix is marked as ephemeral.

    Args:
        base_prompt: The main system prompt that remains constant
        suffix: Optional dynamic additions to the system prompt

    Returns:
        Dict containing the prompt text and cache control metadata
    """
    # Base prompt is persistent as it rarely changes
    result = {"text": base_prompt, "cache_control": {"type": "persistent"}}

    # If there's a suffix, add it as a separate ephemeral block
    if suffix:
        return [result, {"text": suffix, "cache_control": {"type": "ephemeral"}}]

    return result
