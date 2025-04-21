"""
CRUD operations for conversation persistence.

This module provides a repository pattern implementation for
storing and retrieving chats and messages in a SQLite database.
"""

import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import BaseMessage

from vmpilot.db.connection import get_db_connection

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation data operations."""

    def __init__(self):
        """Initialize the repository with a database connection."""
        self.conn = get_db_connection()

    def serialize_messages(self, messages: List[BaseMessage]) -> str:
        """Serialize a list of BaseMessage objects to JSON string."""
        try:
            # Convert each message to a serializable format
            serializable = []
            for msg in messages:
                # Start with a basic representation
                msg_dict = {
                    "type": msg.__class__.__name__,
                    "content": getattr(msg, "content", ""),
                }

                # Use built-in serialization methods if available to get additional fields
                if hasattr(msg, "model_dump"):  # Pydantic v2
                    msg_dict.update(msg.model_dump())
                elif hasattr(msg, "dict"):  # Pydantic v1
                    msg_dict.update(msg.dict())

                serializable.append(msg_dict)

            # Serialize to JSON
            return json.dumps(serializable)
        except Exception as e:
            logger.error(f"Error serializing messages: {e}")
            # Return empty list as fallback
            return "[]"

    def deserialize_messages(self, json_str: str) -> List[BaseMessage]:
        """Deserialize JSON string back to list of BaseMessage objects."""
        try:
            from langchain_core.messages import (
                AIMessage,
                HumanMessage,
                SystemMessage,
                ToolMessage,
            )

            # Parse JSON
            data = json.loads(json_str)

            # Convert each serialized message back to appropriate LangChain message type
            messages = []
            for item in data:
                # Check for explicit type field
                msg_type = item.get("type", "")

                # If type is not explicitly defined, try to determine from class name
                if not msg_type and "type_name" in item:
                    msg_type = item["type_name"]

                # Fall back to trying to determine from the structure
                if not msg_type:
                    # Try to determine the type from the structure
                    if "role" in item:
                        role = item.get("role", "").lower()
                        if role == "user":
                            msg_type = "HumanMessage"
                        elif role == "assistant":
                            msg_type = "AIMessage"
                        elif role == "system":
                            msg_type = "SystemMessage"
                        elif role == "tool":
                            msg_type = "ToolMessage"

                # Get content
                content = item.get("content", "")

                # Normalize message type for comparison
                msg_type_lower = msg_type.lower()

                # Create appropriate message type
                if "human" in msg_type_lower:
                    messages.append(HumanMessage(content=content))
                elif "ai" in msg_type_lower or "assistant" in msg_type_lower:
                    messages.append(AIMessage(content=content))
                elif "system" in msg_type_lower:
                    messages.append(SystemMessage(content=content))
                elif "tool" in msg_type_lower:
                    messages.append(ToolMessage(content=content))
                else:
                    logger.warning(f"Unknown message type: {msg_type}")

            return messages
        except Exception as e:
            logger.error(f"Error deserializing messages: {e}")
            return []

    def save_conversation_state(
        self,
        chat_id: str,
        messages: List[BaseMessage],
        cache_info: Optional[Dict[str, int]] = None,
    ) -> None:
        """
        Save the conversation state for a given chat_id to the database.

        Args:
            chat_id: The unique identifier for the conversation thread
            messages: List of LangChain messages representing the conversation state
            cache_info: Dictionary containing cache token information (optional)
        """
        if chat_id is None:
            logger.warning("Cannot save conversation state: chat_id is None")
            return

        # Default empty cache_info if None
        if cache_info is None:
            cache_info = {}

        # Serialize messages and cache_info
        serialized_messages = self.serialize_messages(messages)
        serialized_cache_info = json.dumps(cache_info)

        cursor = self.conn.cursor()

        # Use INSERT OR REPLACE to handle both new and existing entries
        cursor.execute(
            """
            INSERT OR REPLACE INTO chat_histories
            (chat_id, messages, cache_info, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (chat_id, serialized_messages, serialized_cache_info),
        )

        self.conn.commit()
        logger.debug(
            f"Saved conversation state to database for chat_id {chat_id}: {len(messages)} messages"
        )

    def get_conversation_state(
        self, chat_id: str
    ) -> Tuple[List[BaseMessage], Dict[str, int]]:
        """
        Retrieve the conversation state for a given chat_id from the database.

        Args:
            chat_id: The unique identifier for the conversation thread

        Returns:
            Tuple containing:
            - List of LangChain messages representing the conversation state
            - Dictionary with cache token information
        """
        if chat_id is None:
            logger.warning("Cannot retrieve conversation state: chat_id is None")
            return [], {}

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT messages, cache_info FROM chat_histories
            WHERE chat_id = ?
            """,
            (chat_id,),
        )

        result = cursor.fetchone()
        if result:
            # Deserialize messages and cache_info
            messages = self.deserialize_messages(result[0])
            cache_info = json.loads(result[1])

            logger.debug(
                f"Retrieved conversation state from database for chat_id {chat_id}: {len(messages)} messages"
            )
            return messages, cache_info
        else:
            logger.debug(
                f"No conversation state found in database for chat_id: {chat_id}"
            )
            return [], {}

    def update_cache_info(self, chat_id: str, cache_info: Dict[str, int]) -> None:
        """
        Update only the cache information for a given chat_id in the database.

        Args:
            chat_id: The unique identifier for the conversation thread
            cache_info: Dictionary containing cache token information
        """
        if chat_id is None:
            logger.warning("Cannot update cache info: chat_id is None")
            return

        # Serialize cache_info
        serialized_cache_info = json.dumps(cache_info)

        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE chat_histories
            SET cache_info = ?, updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = ?
            """,
            (serialized_cache_info, chat_id),
        )

        if cursor.rowcount > 0:
            self.conn.commit()
            logger.debug(f"Updated cache info in database for chat_id {chat_id}")
        else:
            logger.warning(
                f"Cannot update cache info: no state exists in database for chat_id {chat_id}"
            )

    def clear_conversation_state(self, chat_id: str) -> None:
        """
        Clear the conversation state for a given chat_id from the database.

        Args:
            chat_id: The unique identifier for the conversation thread
        """
        if chat_id is None:
            logger.warning("Cannot clear conversation state: chat_id is None")
            return

        cursor = self.conn.cursor()
        cursor.execute(
            """
            DELETE FROM chat_histories
            WHERE chat_id = ?
            """,
            (chat_id,),
        )

        self.conn.commit()
        logger.debug(f"Cleared conversation state from database for chat_id {chat_id}")
