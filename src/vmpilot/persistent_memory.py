"""
Persistent conversation state manager for VMPilot using SQLite.
This module provides the same interface as agent_memory.py but uses a database backend.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import BaseMessage

from vmpilot.db.crud import ConversationRepository

# Configure logging
logger = logging.getLogger(__name__)

# Create a single repository instance
_repo = ConversationRepository()


def save_conversation_state(
    thread_id: str,
    messages: List[BaseMessage],
    cache_info: Optional[Dict[str, int]] = None,
) -> None:
    """
    Save the conversation state for a given thread_id to the database.

    Args:
        thread_id: The unique identifier for the conversation thread
        messages: List of LangChain messages representing the conversation state
        cache_info: Dictionary containing cache token information (optional)
    """
    if thread_id is None:
        logger.warning("Cannot save conversation state: thread_id is None")
        return

    # If no cache_info is provided, retrieve any existing cache_info
    if cache_info is None:
        _, existing_cache_info = _repo.get_conversation_state(thread_id)
        cache_info = existing_cache_info or {}
    else:
        # Merge with existing cache_info if it exists
        _, existing_cache_info = _repo.get_conversation_state(thread_id)
        if existing_cache_info:
            # Use the new cache_info but preserve any existing keys not in the new one
            for key, value in existing_cache_info.items():
                if key not in cache_info:
                    cache_info[key] = value

    # Save to database
    _repo.save_conversation_state(thread_id, messages, cache_info)

    logger.debug(
        f"Saved conversation state to database for thread_id {thread_id}: {len(messages)} messages, cache_info: {cache_info}"
    )


def get_conversation_state(thread_id: str) -> Tuple[List[BaseMessage], Dict[str, int]]:
    """
    Retrieve the conversation state for a given thread_id from the database.

    Args:
        thread_id: The unique identifier for the conversation thread

    Returns:
        Tuple containing:
        - List of LangChain messages representing the conversation state
        - Dictionary with cache token information
    """
    if thread_id is None:
        logger.debug(f"No conversation state found for thread_id: None")
        return [], {}

    # Get from database
    messages, cache_info = _repo.get_conversation_state(thread_id)

    from vmpilot.init_agent import modify_state_messages

    # Create a state object similar to what the agent would use
    state = {"messages": messages}

    # Run the messages through modify_state_messages to properly handle cache_control
    messages = modify_state_messages(state)

    logger.debug(
        f"Retrieved conversation state from database for thread_id {thread_id}: {len(messages)} messages, cache_info: {cache_info}"
    )
    return messages, cache_info


def update_cache_info(thread_id: str, cache_info: Dict[str, int]) -> None:
    """
    Update only the cache information for a given thread_id in the database.

    Args:
        thread_id: The unique identifier for the conversation thread
        cache_info: Dictionary containing cache token information
    """
    if thread_id is None:
        logger.warning("Cannot update cache info: thread_id is None")
        return

    # Update in database
    _repo.update_cache_info(thread_id, cache_info)
    logger.debug(
        f"Updated cache info in database for thread_id {thread_id}: {cache_info}"
    )


def clear_conversation_state(thread_id: str) -> None:
    """
    Clear the conversation state for a given thread_id from the database.

    Args:
        thread_id: The unique identifier for the conversation thread
    """
    if thread_id is None:
        logger.warning("Cannot clear conversation state: thread_id is None")
        return

    # Clear from database
    _repo.clear_conversation_state(thread_id)
    logger.debug(f"Cleared conversation state from database for thread_id {thread_id}")
