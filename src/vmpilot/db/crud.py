"""
CRUD operations for conversation persistence.

This module provides a repository pattern implementation for
storing and retrieving chats and messages in a SQLite database.
"""

import json
import logging
import os
import traceback
from typing import Dict, List, Optional, Tuple

from langchain_core.messages import BaseMessage

from vmpilot.db.connection import get_db_connection

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation data operations."""

    def __init__(self):
        """Initialize the repository with a database connection."""
        self.conn = get_db_connection()

    def create_exchange(
        self,
        chat_id: str,
        request: str,
        cost: dict,
        start: str,
        end: str,
    ) -> None:
        """
        Insert a new exchange row into the exchanges table.

        Args:
            chat_id: The chat/thread ID.
            request: The truncated user request.
            cost: Cost info (as dict, will be serialized to JSON).
            start: Start timestamp (ISO string).
            end: End timestamp (ISO string).
        """
        import json

        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO exchanges (chat_id, request, cost, start, end)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    chat_id,
                    request,
                    json.dumps(cost),
                    start,
                    end,
                ),
            )
            self.conn.commit()
            logger.debug(f"Inserted exchange for chat_id={chat_id}")
        except Exception as e:
            logger.error(f"Failed to insert exchange: {e}")
            traceback.print_exc()

    def create_chat(self, chat_id: str, initial_request: Optional[str] = None) -> None:
        """
        Create a new chat record with initial context information.

        Args:
            chat_id: The unique identifier for the chat
            initial_request: The first user message that started the chat (optional)
            project_root: Path to the project directory (optional)
        """

        # Check if this chat already exists with message data
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT chat_id FROM chats WHERE chat_id = ? AND messages IS NOT NULL
            """,
            (chat_id,),
        )

        # If the chat already exists with message data, don't overwrite it
        if cursor.fetchone():
            logger.warning(
                f"Chat {chat_id} already exists with message data, skipping creation"
            )
            return

        # Use empty strings for NULL values to avoid database errors
        initial_request = initial_request or ""
        project_root = os.environ.get("PROJECT_ROOT") or ""

        # Default empty values for required fields
        empty_messages = ""
        empty_cache_info = ""

        cursor.execute(
            """
            INSERT OR REPLACE INTO chats
            (chat_id, initial_request, project_root, messages, cache_info, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (chat_id, initial_request, project_root, empty_messages, empty_cache_info),
        )

        self.conn.commit()
        logger.debug(f"Created new chat record for chat_id {chat_id}")

    def serialize_messages(self, messages: List[BaseMessage]) -> str:
        """Serialize a list of BaseMessage objects to JSON string."""
        from langchain_core.messages import messages_to_dict

        try:
            serializable = messages_to_dict(messages)
            return json.dumps(serializable)
        except Exception as e:
            logger.error(f"Error serializing messages: {e}")
            return "[]"

    def deserialize_messages(self, json_str: str) -> List[BaseMessage]:
        """Deserialize JSON string back to list of BaseMessage objects."""
        from langchain_core.messages import messages_from_dict

        try:
            data = json.loads(json_str)
            messages = messages_from_dict(data)
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

        try:
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
                INSERT OR REPLACE INTO chats
                (chat_id, messages, cache_info, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (chat_id, serialized_messages, serialized_cache_info),
            )

            self.conn.commit()
            logger.debug(
                f"Saved conversation state to database for chat_id {chat_id}: {len(messages)} messages"
            )
        except Exception as e:
            logger.error(f"Error saving conversation state to database: {e}")

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

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT messages, cache_info
                FROM chats
                WHERE chat_id = ?
                order by updated_at desc limit 1
                """,
                (chat_id,),
            )

            result = cursor.fetchone()
            if result:
                # Deserialize messages and cache_info
                serialized_messages = result[0]
                serialized_cache_info = result[1]

                # Handle empty or None message data
                if serialized_messages is None or not serialized_messages:
                    # Initial chat has no messages or NULL value
                    logger.debug(
                        f"Retrieved empty messages for chat_id {chat_id}, returning empty list"
                    )
                    return [], {}

                # Handle empty or None cache info
                if serialized_cache_info is None or not serialized_cache_info:
                    cache_info = {}
                else:
                    try:
                        cache_info = json.loads(serialized_cache_info)
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Error decoding cache info: {e}, using empty dict"
                        )
                        cache_info = {}

                # Deserialize messages
                messages = self.deserialize_messages(serialized_messages)

                logger.debug(
                    f"Retrieved conversation state from database for chat_id {chat_id}: {len(messages)} messages"
                )
                return messages, cache_info
            else:
                logger.debug(
                    f"No conversation state found in database for chat_id: {chat_id}"
                )
                return [], {}
        except Exception as e:
            logger.error(f"Error retrieving conversation state from database: {e}")
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
            UPDATE chats
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
            DELETE FROM chats
            WHERE chat_id = ?
            """,
            (chat_id,),
        )

        self.conn.commit()
        logger.debug(f"Cleared conversation state from database for chat_id {chat_id}")
