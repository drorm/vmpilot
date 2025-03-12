"""
CRUD operations for VMPilot conversation persistence.
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .connection import get_db_connection

# Configure logging
logger = logging.getLogger(__name__)


class ConversationRepository:
    """
    Repository for conversation persistence operations.
    Handles CRUD operations for conversations and messages.
    """

    def __init__(self):
        """Initialize the repository with a database connection."""
        self.conn = get_db_connection()

    def save_conversation(
        self, conversation_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a new conversation or update an existing one.

        Args:
            conversation_id: Unique identifier for the conversation
            metadata: Optional metadata for the conversation (will be stored as JSON)

        Returns:
            True if successful, False otherwise
        """
        try:
            metadata_json = json.dumps(metadata) if metadata else None

            with self.conn:
                # Use INSERT OR REPLACE to handle both new and existing conversations
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO chats (id, metadata)
                    VALUES (?, ?);
                    """,
                    (conversation_id, metadata_json),
                )

            logger.debug(f"Saved conversation: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving conversation {conversation_id}: {str(e)}")
            return False

    def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Save a message in a conversation.

        Args:
            conversation_id: ID of the conversation this message belongs to
            role: Role of the message sender ('user', 'assistant', 'system')
            content: Text content of the message
            message_id: Optional unique identifier for the message
            metadata: Optional metadata for the message (will be stored as JSON)

        Returns:
            ID of the inserted message, or None if insertion failed
        """
        try:
            # Ensure the conversation exists
            self.save_conversation(conversation_id)

            metadata_json = json.dumps(metadata) if metadata else None

            with self.conn:
                cursor = self.conn.execute(
                    """
                    INSERT INTO messages (conversation_id, role, content, message_id, metadata)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (conversation_id, role, content, message_id, metadata_json),
                )

            message_id = cursor.lastrowid
            logger.debug(
                f"Saved message {message_id} in conversation {conversation_id}"
            )
            return message_id

        except Exception as e:
            logger.error(
                f"Error saving message in conversation {conversation_id}: {str(e)}"
            )
            return None

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: ID of the conversation to retrieve

        Returns:
            Dictionary with conversation data, or None if not found
        """
        try:
            cursor = self.conn.execute(
                "SELECT id, created_at, metadata FROM chats WHERE id = ?;",
                (conversation_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            conversation = dict(row)

            # Parse metadata JSON if present
            if conversation["metadata"]:
                conversation["metadata"] = json.loads(conversation["metadata"])
            else:
                conversation["metadata"] = {}

            return conversation

        except Exception as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {str(e)}")
            return None

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            List of message dictionaries
        """
        try:
            cursor = self.conn.execute(
                """
                SELECT id, conversation_id, role, content, created_at, message_id, metadata
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id ASC;
                """,
                (conversation_id,),
            )

            messages = []
            for row in cursor:
                message = dict(row)

                # Parse metadata JSON if present
                if message["metadata"]:
                    message["metadata"] = json.loads(message["metadata"])
                else:
                    message["metadata"] = {}

                messages.append(message)

            return messages

        except Exception as e:
            logger.error(
                f"Error retrieving messages for conversation {conversation_id}: {str(e)}"
            )
            return []

    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """
        Get all conversations.

        Returns:
            List of conversation dictionaries
        """
        try:
            cursor = self.conn.execute(
                "SELECT id, created_at, metadata FROM chats ORDER BY created_at DESC;"
            )

            conversations = []
            for row in cursor:
                conversation = dict(row)

                # Parse metadata JSON if present
                if conversation["metadata"]:
                    conversation["metadata"] = json.loads(conversation["metadata"])
                else:
                    conversation["metadata"] = {}

                conversations.append(conversation)

            return conversations

        except Exception as e:
            logger.error(f"Error retrieving all conversations: {str(e)}")
            return []

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.conn:
                # Delete messages first due to foreign key constraint
                self.conn.execute(
                    "DELETE FROM messages WHERE conversation_id = ?;",
                    (conversation_id,),
                )

                # Then delete the conversation
                self.conn.execute(
                    "DELETE FROM chats WHERE id = ?;",
                    (conversation_id,),
                )

            logger.debug(f"Deleted conversation: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return False


# Singleton instance
_repository: Optional[ConversationRepository] = None


def get_repository() -> ConversationRepository:
    """
    Get the singleton repository instance.

    Returns:
        ConversationRepository instance
    """
    global _repository

    if _repository is None:
        _repository = ConversationRepository()

    return _repository
