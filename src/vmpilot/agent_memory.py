"""
Conversation state manager for VMPilot.
Persists conversations to database while maintaining in-memory cache.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import BaseMessage

from vmpilot.db.crud import get_repository

# Configure logging
logger = logging.getLogger(__name__)

# Global dictionary to store conversation states by thread_id
# Keys are thread_ids, values are dictionaries containing messages and cache info
# This serves as an in-memory cache for faster access
conversation_states: Dict[str, Dict[str, Any]] = {}

# Get the database repository
repository = get_repository()


def save_conversation_state(
    thread_id: str,
    messages: List[BaseMessage],
    cache_info: Optional[Dict[str, int]] = None,
) -> None:
    """
    Save the conversation state for a given thread_id.
    Persists to both in-memory cache and database.

    Args:
        thread_id: The unique identifier for the conversation thread
        messages: List of LangChain messages representing the conversation state
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

    # Update in-memory cache
    conversation_states[thread_id] = {"messages": messages, "cache_info": cache_info}

    # Save to database - first save/update the conversation
    metadata = {"cache_info": json.dumps(cache_info)} if cache_info else {}
    repository.save_conversation(conversation_id=thread_id, metadata=metadata)

    # Then save all messages
    for i, message in enumerate(messages):
        # Convert LangChain message to a format suitable for database storage
        role = message.type

        # Convert content to string if it's a complex type (like a list)
        if isinstance(message.content, (list, dict)):
            content = json.dumps(message.content)
        else:
            content = str(message.content)

        # Prepare message metadata
        message_metadata = {}

        # Store tool name in metadata for tool messages
        if role == "tool":
            if hasattr(message, "name"):
                message_metadata["name"] = message.name

            # Store tool_call_id if present (for newer LangChain versions)
            if hasattr(message, "tool_call_id") and message.tool_call_id:
                message_metadata["tool_call_id"] = message.tool_call_id

        try:
            repository.save_message(
                conversation_id=thread_id,
                role=role,
                content=content,
                message_id=str(i),
                metadata=message_metadata,
            )
        except Exception as e:
            logger.error(f"Error saving message in conversation {thread_id}: {e}")

    logger.info(
        f"Saved conversation state for thread_id {thread_id}: {len(messages)} messages, cache_info: {cache_info}"
    )


def get_conversation_state(thread_id: str) -> Tuple[List[BaseMessage], Dict[str, int]]:
    """
    Retrieve the conversation state for a given thread_id.
    First checks in-memory cache, then falls back to database if needed.

    Args:
        thread_id: The unique identifier for the conversation thread

    Returns:
        Tuple containing:
        - List of LangChain messages representing the conversation state
        - Dictionary with cache token information
    """
    if thread_id is None:
        logger.info(f"Cannot retrieve conversation state: thread_id is None")
        return [], {}

    # Check in-memory cache first
    if thread_id in conversation_states:
        state = conversation_states[thread_id]
        messages = state.get("messages", [])
        cache_info = state.get("cache_info", {})

        logger.info(
            f"Retrieved conversation state from memory for thread_id {thread_id}: {len(messages)} messages"
        )
        return messages, cache_info

    # If not in memory, try to load from database
    try:
        # Get conversation metadata from database
        conversation = repository.get_conversation(thread_id)
        if not conversation:
            logger.info(f"No conversation found in database for thread_id: {thread_id}")
            return [], {}

        # Get cache_info from metadata
        cache_info = {}
        if conversation.get("metadata") and "cache_info" in conversation["metadata"]:
            try:
                cache_info = json.loads(conversation["metadata"]["cache_info"])
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse cache_info for thread_id {thread_id}")

        # Get messages from database
        db_messages = repository.get_messages(thread_id)

        # Convert database messages to LangChain format
        from langchain_core.messages import (
            HumanMessage,
            AIMessage,
            SystemMessage,
            ToolMessage,
        )

        messages = []
        for msg in db_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Try to detect and parse JSON content
            if content and (content.startswith("[") or content.startswith("{")):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    # If it's not valid JSON, keep it as is
                    pass

            # Create appropriate message type based on role
            if role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "ai" or role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "tool":
                # Get tool name and tool_call_id from metadata if available
                tool_name = ""
                tool_call_id = ""
                if msg.get("metadata"):
                    if "name" in msg["metadata"]:
                        tool_name = msg["metadata"]["name"]
                    if "tool_call_id" in msg["metadata"]:
                        tool_call_id = msg["metadata"]["tool_call_id"]

                # Create ToolMessage with appropriate parameters
                # Note: Different versions of LangChain may require different parameters
                try:
                    # First try with all parameters
                    messages.append(
                        ToolMessage(
                            content=content, name=tool_name, tool_call_id=tool_call_id
                        )
                    )
                except TypeError as e:
                    # If that fails, try without tool_call_id
                    logger.debug(f"Trying alternative ToolMessage construction: {e}")
                    try:
                        messages.append(ToolMessage(content=content, name=tool_name))
                    except Exception as e2:
                        logger.error(f"Failed to create ToolMessage: {e2}")
                        # Fall back to AIMessage to prevent breaking the conversation
                        messages.append(
                            AIMessage(content=f"Tool Result ({tool_name}): {content}")
                        )
            else:
                logger.warning(f"Unknown message role '{role}' in thread {thread_id}")

        # Update in-memory cache
        conversation_states[thread_id] = {
            "messages": messages,
            "cache_info": cache_info,
        }

        logger.info(
            f"Retrieved conversation state from database for thread_id {thread_id}: {len(messages)} messages"
        )
        return messages, cache_info

    except Exception as e:
        logger.error(f"Error retrieving conversation from database: {e}")
        return [], {}


def update_cache_info(thread_id: str, cache_info: Dict[str, int]) -> None:
    """
    Update only the cache information for a given thread_id.
    Updates both in-memory cache and database.

    Args:
        thread_id: The unique identifier for the conversation thread
        cache_info: Dictionary containing cache token information
    """
    if thread_id is None:
        logger.warning("Cannot update cache info: thread_id is None")
        return

    # Update in-memory cache if it exists
    if thread_id in conversation_states:
        conversation_states[thread_id]["cache_info"] = cache_info
        logger.info(
            f"Updated cache info in memory for thread_id {thread_id}: {cache_info}"
        )
    else:
        logger.warning(
            f"Cannot update cache info in memory: no state exists for thread_id {thread_id}"
        )

    # Update in database
    try:
        # First check if conversation exists
        conversation = repository.get_conversation(thread_id)
        if conversation:
            # Update the conversation with new cache_info
            metadata = {"cache_info": json.dumps(cache_info)}
            repository.save_conversation(conversation_id=thread_id, metadata=metadata)
            logger.info(f"Updated cache info in database for thread_id {thread_id}")
        else:
            logger.warning(
                f"Cannot update cache info in database: no conversation exists for thread_id {thread_id}"
            )
    except Exception as e:
        logger.error(f"Error updating cache info in database: {e}")


def clear_conversation_state(thread_id: str) -> None:
    """
    Clear the conversation state for a given thread_id.
    Removes from both in-memory cache and database.

    Args:
        thread_id: The unique identifier for the conversation thread
    """
    # Clear from in-memory cache
    if thread_id in conversation_states:
        del conversation_states[thread_id]
        logger.info(f"Cleared conversation state from memory for thread_id {thread_id}")

    # Delete from database
    try:
        success = repository.delete_conversation(thread_id)
        if success:
            logger.info(f"Deleted conversation from database for thread_id {thread_id}")
        else:
            logger.warning(
                f"Failed to delete conversation from database for thread_id {thread_id}"
            )
    except Exception as e:
        logger.error(f"Error deleting conversation from database: {e}")
