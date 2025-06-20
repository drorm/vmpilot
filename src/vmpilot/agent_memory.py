"""
In-memory conversation state manager for VMPilot.
This is a simple implementation to verify the caching fix approach.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Global dictionary to store conversation states by thread_id
# Keys are thread_ids, values are dictionaries containing messages and cache info
conversation_states: Dict[str, Dict[str, Any]] = {}


def save_conversation_state(
    thread_id: str,
    messages: List[Dict[str, Any]],
    cache_info: Optional[Dict[str, int]] = None,
) -> None:
    """
    Save the conversation state for a given thread_id.

    Args:
        thread_id: The unique identifier for the conversation thread
        messages: List of messages representing the conversation state
        cache_info: Dictionary containing cache token information (optional)
    """
    if thread_id is None:
        logger.warning("Cannot save conversation state: thread_id is None")
        return

    # If no cache_info is provided, preserve any existing cache_info
    if cache_info is None and thread_id in conversation_states:
        cache_info = conversation_states[thread_id].get("cache_info", {})
    elif cache_info is None:
        cache_info = {}

    conversation_states[thread_id] = {"messages": messages, "cache_info": cache_info}

    logger.debug(
        f"Saved conversation state for thread_id {thread_id}: {len(messages)} messages, cache_info: {cache_info}"
    )


def get_conversation_state(
    thread_id: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Retrieve the conversation state for a given thread_id.

    Args:
        thread_id: The unique identifier for the conversation thread

    Returns:
        Tuple containing:
        - List of messages representing the conversation state
        - Dictionary with cache token information
    """
    if thread_id is None or thread_id not in conversation_states:
        logger.debug(f"No conversation state found for thread_id: {thread_id}")
        return [], {}

    state = conversation_states.get(thread_id, {"messages": [], "cache_info": {}})
    messages = state.get("messages", [])
    cache_info = state.get("cache_info", {})

    logger.debug(
        f"Retrieved conversation state for thread_id {thread_id}: {len(messages)} messages, cache_info: {cache_info}"
    )
    return messages, cache_info


def update_cache_info(thread_id: str, cache_info: Dict[str, int]) -> None:
    """
    Update only the cache information for a given thread_id.

    Args:
        thread_id: The unique identifier for the conversation thread
        cache_info: Dictionary containing cache token information
    """
    if thread_id is None:
        logger.warning("Cannot update cache info: thread_id is None")
        return

    if thread_id in conversation_states:
        conversation_states[thread_id]["cache_info"] = cache_info
        logger.debug(f"Updated cache info for thread_id {thread_id}: {cache_info}")
    else:
        logger.warning(
            f"Cannot update cache info: no state exists for thread_id {thread_id}"
        )


def clear_conversation_state(thread_id: str) -> None:
    """
    Clear the conversation state for a given thread_id.

    Args:
        thread_id: The unique identifier for the conversation thread
    """
    if thread_id in conversation_states:
        del conversation_states[thread_id]
        logger.debug(f"Cleared conversation state for thread_id {thread_id}")
