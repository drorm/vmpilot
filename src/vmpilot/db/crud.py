"""
CRUD operations for conversation persistence.

This module provides a repository pattern implementation for
storing and retrieving conversations and exchanges from the SQLite database.
"""

import json
import pickle
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from vmpilot.db.connection import get_db_connection

T = TypeVar("T")


class ConversationRepository:
    """Repository for conversation data operations."""

    def __init__(self):
        """Initialize the repository with a database connection."""
        self.conn = get_db_connection()

        # Ensure tables exist
        from vmpilot.db.connection import initialize_db

        initialize_db()

    def save_chat(
        self,
        chat_id: str,
        initial_request: Optional[str] = None,
        project_root: Optional[str] = None,
        current_issue: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create or update a chat in the database.

        Args:
            chat_id: Unique identifier for the chat
            initial_request: The first user message that started the chat
            project_root: Path to the project directory
            current_issue: Current issue being worked on
            metadata: Optional metadata for the chat

        Returns:
            str: The chat_id of the created/updated chat
        """
        cursor = self.conn.cursor()
        metadata_json = json.dumps(metadata) if metadata else None

        # Check if chat exists
        cursor.execute("SELECT id FROM chats WHERE id = ?", (chat_id,))
        if cursor.fetchone():
            # Update existing chat
            cursor.execute(
                """
                UPDATE chats 
                SET initial_request = COALESCE(?, initial_request),
                    project_root = COALESCE(?, project_root),
                    current_issue = COALESCE(?, current_issue),
                    metadata = COALESCE(?, metadata)
                WHERE id = ?
                """,
                (initial_request, project_root, current_issue, metadata_json, chat_id),
            )
        else:
            # Create new chat
            cursor.execute(
                """
                INSERT INTO chats 
                (id, initial_request, project_root, current_issue, metadata) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, initial_request, project_root, current_issue, metadata_json),
            )

        self.conn.commit()
        return chat_id

    def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chat by its ID.

        Args:
            chat_id: The ID of the chat

        Returns:
            Optional[Dict[str, Any]]: Chat data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))

        row = cursor.fetchone()
        if not row:
            return None

        chat = dict(row)
        if chat.get("metadata"):
            chat["metadata"] = json.loads(chat["metadata"])

        return chat

    def save_exchange(
        self,
        chat_id: str,
        user_message: str,
        assistant_response: Optional[str] = None,
        tool_calls: Optional[Dict[str, Any]] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        serialized_exchange: Optional[str] = None,
    ) -> int:
        """
        Save a complete exchange to the database.

        Args:
            chat_id: The ID of the chat
            user_message: The user's message content
            assistant_response: The assistant's response content
            tool_calls: JSON-serializable dictionary of tool calls made
            started_at: When the exchange started (defaults to now)
            completed_at: When the exchange completed (defaults to None)
            serialized_exchange: Full serialized Exchange object

        Returns:
            int: The ID of the saved exchange
        """
        # Ensure the chat exists
        self.save_chat(chat_id)

        cursor = self.conn.cursor()

        # Default started_at to now if not provided
        if started_at is None:
            started_at = datetime.now()

        # Serialize tool calls if provided
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None

        cursor.execute(
            """
            INSERT INTO exchanges 
            (chat_id, user_message, assistant_response, tool_calls, 
             started_at, completed_at, serialized_exchange)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                user_message,
                assistant_response,
                tool_calls_json,
                started_at,
                completed_at,
                serialized_exchange,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chat by its ID.

        Args:
            chat_id: The ID of the chat

        Returns:
            Optional[Dict[str, Any]]: The chat data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
        row = cursor.fetchone()

        if not row:
            return None

        chat = dict(row)
        if chat.get("metadata"):
            chat["metadata"] = json.loads(chat["metadata"])

        return chat

    def get_exchanges_for_chat(
        self, chat_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all exchanges for a chat.

        Args:
            chat_id: The ID of the chat
            limit: Maximum number of exchanges to retrieve
            offset: Offset for pagination

        Returns:
            List[Dict[str, Any]]: List of exchanges in the chat
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM exchanges 
            WHERE chat_id = ? 
            ORDER BY started_at 
            LIMIT ? OFFSET ?
            """,
            (chat_id, limit, offset),
        )

        exchanges = []
        for row in cursor.fetchall():
            exchange = dict(row)

            # Parse JSON fields
            if exchange.get("tool_calls"):
                exchange["tool_calls"] = json.loads(exchange["tool_calls"])

            exchanges.append(exchange)

        return exchanges

    def save_chat_history(
        self, chat_id: str, full_history: List[Dict[str, Any]]
    ) -> int:
        """
        Save the complete chat history for a chat.

        This method stores the entire conversation history for faster retrieval
        instead of reconstructing it from individual exchanges.

        Args:
            chat_id: The ID of the chat
            full_history: The complete chat history as a list of message dictionaries

        Returns:
            int: The ID of the newly inserted chat history record
        """
        cursor = self.conn.cursor()

        # Serialize the full history to JSON
        serialized_history = json.dumps(full_history)
        message_count = len(full_history)

        cursor.execute(
            """
            INSERT INTO chat_histories 
            (chat_id, full_history, message_count) 
            VALUES (?, ?, ?)
            """,
            (chat_id, serialized_history, message_count),
        )

        self.conn.commit()
        return cursor.lastrowid

    def get_latest_chat_history(self, chat_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get the most recent chat history for a chat.

        Args:
            chat_id: The ID of the chat

        Returns:
            Optional[List[Dict[str, Any]]]: The complete chat history as a list of message
            dictionaries, or None if no history exists
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT full_history FROM chat_histories 
            WHERE chat_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
            """,
            (chat_id,),
        )

        result = cursor.fetchone()
        if result and result["full_history"]:
            try:
                history = json.loads(result["full_history"])
                # Log the history to help with debugging
                import logging

                logger = logging.getLogger(__name__)
                logger.debug(
                    f"Retrieved history from database for {chat_id}: {len(history)} messages"
                )
                return history
            except json.JSONDecodeError as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Error decoding chat history JSON: {e}")
                return None
        return None

    def get_chats(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a list of chats.

        Args:
            limit: Maximum number of chats to retrieve
            offset: Offset for pagination

        Returns:
            List[Dict[str, Any]]: List of chats
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM chats ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )

        chats = []
        for row in cursor.fetchall():
            chat = dict(row)
            if chat.get("metadata"):
                chat["metadata"] = json.loads(chat["metadata"])
            chats.append(chat)

        return chats

    def delete_chat(self, chat_id: str) -> bool:
        """
        Delete a chat and all its exchanges.

        Args:
            chat_id: The ID of the chat

        Returns:
            bool: True if the chat was deleted, False otherwise
        """
        cursor = self.conn.cursor()

        # Delete exchanges first due to foreign key constraint
        cursor.execute("DELETE FROM exchanges WHERE chat_id = ?", (chat_id,))
        cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))

        self.conn.commit()
        return cursor.rowcount > 0

    def format_exchanges_for_langchain(
        self, chat_id: str
    ) -> List[Dict[str, Union[str, Dict[str, Any]]]]:
        """
        Format chat exchanges for use with LangChain.

        Args:
            chat_id: The ID of the chat

        Returns:
            List[Dict[str, Union[str, Dict[str, Any]]]]: Messages formatted for LangChain
        """
        exchanges = self.get_exchanges_for_chat(chat_id)
        formatted_messages = []

        for exchange in exchanges:
            # Add user message
            formatted_messages.append(
                {
                    "type": "human",
                    "data": {
                        "content": exchange["user_message"],
                        "additional_kwargs": {},
                    },
                }
            )

            # Add assistant response if available
            if exchange.get("assistant_response"):
                formatted_messages.append(
                    {
                        "type": "ai",
                        "data": {
                            "content": exchange["assistant_response"],
                            "additional_kwargs": {
                                "tool_calls": exchange.get("tool_calls", {})
                            },
                        },
                    }
                )

        return formatted_messages
