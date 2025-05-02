"""
Unit tests for the database CRUD operations.

Tests the CRUD operations for conversation persistence.
"""

import json
import sqlite3
import unittest
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from vmpilot.db.crud import ConversationRepository


class TestConversationRepositoryCRUD(unittest.TestCase):
    """Test cases for ConversationRepository CRUD operations."""

    def setUp(self):
        """Set up test environment."""
        # Create an in-memory database for testing
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row

        # Create the chats table
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                initial_request TEXT,
                project_root TEXT,
                messages TEXT NOT NULL DEFAULT '',
                cache_info TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.conn.commit()

        # Create a repository with the in-memory connection
        self.repo = ConversationRepository()
        self.repo.conn = self.conn

        # Sample data for testing
        self.chat_id = "test-chat-123"
        self.messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Hello, how are you?"),
            AIMessage(content="I'm doing well, thank you for asking!"),
        ]
        self.cache_info = {"input_tokens": 10, "output_tokens": 20}

    def tearDown(self):
        """Clean up test environment."""
        self.conn.close()

    def test_create_chat(self):
        """Test creating a new chat record."""
        # Create a chat
        self.repo.create_chat(self.chat_id, "Initial request")

        # Verify that the chat was created
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM chats WHERE chat_id = ?", (self.chat_id,))
        result = cursor.fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result["chat_id"], self.chat_id)
        self.assertEqual(result["initial_request"], "Initial request")
        self.assertEqual(result["messages"], "")
        self.assertEqual(result["cache_info"], "")

    def test_create_chat_existing_with_messages(self):
        """Test creating a chat that already exists with messages."""
        # First, create a chat with messages
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO chats (chat_id, initial_request, messages, cache_info)
            VALUES (?, ?, ?, ?)
            """,
            (self.chat_id, "Original request", "existing messages", "{}"),
        )
        self.conn.commit()

        # Now try to create the same chat again
        self.repo.create_chat(self.chat_id, "New request")

        # Verify that the original chat was not overwritten
        cursor.execute("SELECT * FROM chats WHERE chat_id = ?", (self.chat_id,))
        result = cursor.fetchone()

        self.assertEqual(result["initial_request"], "Original request")
        self.assertEqual(result["messages"], "existing messages")

    def test_create_chat_without_initial_request(self):
        """Test creating a chat without an initial request."""
        # Create a chat with no initial request
        self.repo.create_chat(self.chat_id)

        # Verify that the chat was created with an empty initial request
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM chats WHERE chat_id = ?", (self.chat_id,))
        result = cursor.fetchone()

        self.assertEqual(result["initial_request"], "")

    @patch("vmpilot.db.crud.logger")
    def test_save_conversation_state_with_error(self, mock_logger):
        """Test handling errors when saving conversation state."""
        # Use patch to make the method raise an exception
        with patch.object(
            self.repo, "serialize_messages", side_effect=Exception("Database error")
        ):
            # Call the method
            self.repo.save_conversation_state(
                self.chat_id, self.messages, self.cache_info
            )

            # Verify that the error was logged
            mock_logger.error.assert_called_once()
            self.assertIn(
                "Error saving conversation state", mock_logger.error.call_args[0][0]
            )

    def test_get_conversation_state_with_empty_messages(self):
        """Test retrieving a conversation state with empty messages."""
        # Create a chat with empty messages
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO chats (chat_id, initial_request, messages, cache_info)
            VALUES (?, ?, ?, ?)
            """,
            (self.chat_id, "Initial request", "", "{}"),
        )
        self.conn.commit()

        # Retrieve the conversation state
        messages, cache_info = self.repo.get_conversation_state(self.chat_id)

        # Verify that an empty list and empty dict are returned
        self.assertEqual(len(messages), 0)
        self.assertEqual(cache_info, {})

    def test_get_conversation_state_with_invalid_cache_info(self):
        """Test retrieving a conversation state with invalid cache info JSON."""
        # Create a chat with invalid cache info
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO chats (chat_id, initial_request, messages, cache_info)
            VALUES (?, ?, ?, ?)
            """,
            (
                self.chat_id,
                "Initial request",
                self.repo.serialize_messages(self.messages),
                "invalid json",
            ),
        )
        self.conn.commit()

        # Retrieve the conversation state
        messages, cache_info = self.repo.get_conversation_state(self.chat_id)

        # Verify that the messages are retrieved but cache_info is an empty dict
        self.assertEqual(len(messages), 3)
        self.assertEqual(cache_info, {})

    @patch("vmpilot.db.crud.logger")
    def test_get_conversation_state_with_error(self, mock_logger):
        """Test handling errors when retrieving conversation state."""
        # Replace the connection with a MagicMock
        original_conn = self.repo.conn
        try:
            # Create a mock connection that raises an exception when cursor is called
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Database error")

            # Replace the connection
            self.repo.conn = mock_conn

            # Call the method
            messages, cache_info = self.repo.get_conversation_state(self.chat_id)

            # Verify that the error was logged and empty results returned
            mock_logger.error.assert_called_once()
            self.assertIn(
                "Error retrieving conversation state", mock_logger.error.call_args[0][0]
            )
            self.assertEqual(len(messages), 0)
            self.assertEqual(cache_info, {})
        finally:
            # Restore the original connection
            self.repo.conn = original_conn

    def test_update_cache_info(self):
        """Test updating cache info for an existing conversation."""
        # Create a chat
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO chats (chat_id, initial_request, messages, cache_info)
            VALUES (?, ?, ?, ?)
            """,
            (
                self.chat_id,
                "Initial request",
                self.repo.serialize_messages(self.messages),
                json.dumps(self.cache_info),
            ),
        )
        self.conn.commit()

        # Update the cache info
        new_cache_info = {"input_tokens": 30, "output_tokens": 40}
        self.repo.update_cache_info(self.chat_id, new_cache_info)

        # Verify that the cache info was updated
        cursor.execute(
            "SELECT cache_info FROM chats WHERE chat_id = ?", (self.chat_id,)
        )
        result = cursor.fetchone()

        self.assertEqual(json.loads(result["cache_info"]), new_cache_info)

    def test_clear_conversation_state(self):
        """Test clearing a conversation state."""
        # Create a chat
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO chats (chat_id, initial_request, messages, cache_info)
            VALUES (?, ?, ?, ?)
            """,
            (
                self.chat_id,
                "Initial request",
                self.repo.serialize_messages(self.messages),
                json.dumps(self.cache_info),
            ),
        )
        self.conn.commit()

        # Clear the conversation state
        self.repo.clear_conversation_state(self.chat_id)

        # Verify that the chat was deleted
        cursor.execute("SELECT * FROM chats WHERE chat_id = ?", (self.chat_id,))
        result = cursor.fetchone()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
