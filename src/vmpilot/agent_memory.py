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
    tool_call_id_map = {}  # Store mapping of message index to tool_call_id

    # First pass: identify tool_call_ids from AI messages with tool_use
    for i, message in enumerate(messages):
        if message.type == "ai" and isinstance(message.content, list):
            for item in message.content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_id = item.get("id")
                    if tool_id:
                        # Store the tool_use id for the next tool message
                        tool_call_id_map[i + 1] = tool_id

    # Second pass: save all messages with correct metadata
    for i, message in enumerate(messages):
        # Convert LangChain message to a format suitable for database storage
        role = message.type

        # Convert content to string if it's a complex type (like a list)
        if isinstance(message.content, (list, dict)):
            content = json.dumps(message.content)
        else:
            content = str(message.content)

        # Store additional metadata for tool messages
        metadata = None
        if role == "tool" and i > 0:
            # If this is a tool message, store its tool_call_id
            if i - 1 in tool_call_id_map:
                metadata = {"tool_call_id": tool_call_id_map[i - 1]}

        try:
            repository.save_message(
                conversation_id=thread_id,
                role=role,
                content=content,
                message_id=str(i),
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Error saving message in conversation {thread_id}: {e}")

    logger.debug(
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
        logger.debug(f"Cannot retrieve conversation state: thread_id is None")
        return [], {}

    # Check in-memory cache first
    if thread_id in conversation_states:
        state = conversation_states[thread_id]
        messages = state.get("messages", [])
        cache_info = state.get("cache_info", {})

        logger.debug(
            f"Retrieved conversation state from memory for thread_id {thread_id}: {len(messages)} messages"
        )
        return messages, cache_info

    # If not in memory, try to load from database
    try:
        # Get conversation metadata from database
        conversation = repository.get_conversation(thread_id)
        if not conversation:
            logger.debug(
                f"No conversation found in database for thread_id: {thread_id}"
            )
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
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

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

            # Clean up any cache_control attributes in content
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "cache_control" in item:
                        del item["cache_control"]
            elif isinstance(content, dict) and "cache_control" in content:
                del content["cache_control"]

            # Create appropriate message type based on role
            if role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "ai" or role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "tool":
                # Handle tool messages from the database
                from langchain_core.messages import ToolMessage

                # Get the tool_call_id from metadata if available
                tool_call_id = None
                if msg.get("metadata") and "tool_call_id" in msg["metadata"]:
                    tool_call_id = msg["metadata"]["tool_call_id"]

                # If no tool_call_id in metadata, try to extract from previous AI message
                if not tool_call_id and len(messages) > 0:
                    prev_msg = messages[-1]
                    if hasattr(prev_msg, "content") and isinstance(
                        prev_msg.content, list
                    ):
                        for item in prev_msg.content:
                            if (
                                isinstance(item, dict)
                                and item.get("type") == "tool_use"
                            ):
                                tool_call_id = item.get("id")
                                break

                # If still no tool_call_id, use a default
                if not tool_call_id:
                    tool_call_id = "tool_" + str(len(messages))

                # Use a sensible name for the tool
                tool_name = "shell"  # Default to shell as it's the most common tool

                messages.append(
                    ToolMessage(
                        content=content, name=tool_name, tool_call_id=tool_call_id
                    )
                )
            else:
                logger.warning(f"Unknown message role '{role}' in thread {thread_id}")

        # Update in-memory cache
        conversation_states[thread_id] = {
            "messages": messages,
            "cache_info": cache_info,
        }

        logger.debug(
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
        logger.debug(
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
            logger.debug(f"Updated cache info in database for thread_id {thread_id}")
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
        logger.debug(
            f"Cleared conversation state from memory for thread_id {thread_id}"
        )

    # Delete from database
    try:
        success = repository.delete_conversation(thread_id)
        if success:
            logger.debug(
                f"Deleted conversation from database for thread_id {thread_id}"
            )
        else:
            logger.warning(
                f"Failed to delete conversation from database for thread_id {thread_id}"
            )
    except Exception as e:
        logger.error(f"Error deleting conversation from database: {e}")
