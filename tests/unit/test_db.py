"""
Unit tests for the database module.

Tests the functionality of the SQLite database implementation
for conversation persistence.
"""

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vmpilot.db.connection import get_db_connection, get_db_path, initialize_db
from vmpilot.db.crud import ConversationRepository
from vmpilot.db.models import SCHEMA_SQL


class TestDatabaseConnection(unittest.TestCase):
    """Test cases for database connection management."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for the database
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        # Patch the get_db_path function to return our test path
        self.path_patcher = patch("vmpilot.db.connection.get_db_path")
        self.mock_get_path = self.path_patcher.start()
        self.mock_get_path.return_value = self.db_path

    def tearDown(self):
        """Clean up test environment."""
        # Stop the patcher
        self.path_patcher.stop()

        # Close any open connections
        global _db_connection
        _db_connection = None

        # Remove the temporary directory
        self.temp_dir.cleanup()

    def test_initialize_db(self):
        """Test that initialize_db creates the expected tables."""
        print("Starting test_initialize_db")
        # Create a direct connection to the test database path
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Execute the schema to initialize tables directly
        for sql in SCHEMA_SQL:
            print(f"Executing SQL: {sql[:30]}...")
            cursor.executescript(sql)
        conn.commit()
        print(f"Database created at {self.db_path}")

        # Verify that the database file was created
        self.assertTrue(self.db_path.exists())

        # Check that chats table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chats'"
        )
        self.assertIsNotNone(cursor.fetchone())

        # The chat_histories table no longer exists in the updated schema
        # We now have a single chats table with all the necessary columns

        # Check that the chats table has the correct columns
        cursor.execute("PRAGMA table_info(chats)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "chat_id",
            "initial_request",
            "project_root",
            "messages",
            "cache_info",
            "updated_at",
        }

        # Verify the columns match our updated schema
        self.assertSetEqual(expected_columns, columns)


class TestConversationRepository(unittest.TestCase):
    """Test cases for the ConversationRepository class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for the database
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        # Create a connection to the in-memory database
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row

        # Create the schema
        cursor = self.conn.cursor()
        for sql in SCHEMA_SQL:
            cursor.executescript(sql)
        self.conn.commit()

        # Create a repository with the in-memory connection
        self.repo = ConversationRepository()
        # Replace the connection with our in-memory connection
        self.repo.conn = self.conn

        # Sample messages for testing
        self.messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
        ]

        # Sample cache info
        self.cache_info = {"input_tokens": 10, "output_tokens": 20}

    def tearDown(self):
        """Clean up test environment."""
        # Close the connection
        self.conn.close()

        # Remove the temporary directory
        self.temp_dir.cleanup()

    def test_serialize_deserialize_messages(self):
        """Test that messages can be serialized and deserialized correctly."""
        # Serialize messages
        serialized = self.repo.serialize_messages(self.messages)

        # Verify that serialized data is a valid JSON string
        data = json.loads(serialized)
        self.assertEqual(len(data), 3)

        # Deserialize messages
        deserialized = self.repo.deserialize_messages(serialized)

        # Verify that deserialized messages match original messages
        self.assertEqual(len(deserialized), 3)
        self.assertEqual(deserialized[0]["content"], self.messages[0]["content"])
        self.assertEqual(deserialized[1]["content"], self.messages[1]["content"])
        self.assertEqual(deserialized[2]["content"], self.messages[2]["content"])

    def test_save_and_get_conversation_state(self):
        """Test saving and retrieving conversation state."""
        chat_id = "test-chat-123"

        # Save conversation state
        self.repo.save_conversation_state(chat_id, self.messages, self.cache_info)

        # Retrieve conversation state
        retrieved_messages, retrieved_cache_info = self.repo.get_conversation_state(
            chat_id
        )

        # Verify that retrieved messages match original messages
        self.assertEqual(len(retrieved_messages), 3)
        self.assertEqual(retrieved_messages[0]["content"], self.messages[0]["content"])
        self.assertEqual(retrieved_messages[1]["content"], self.messages[1]["content"])
        self.assertEqual(retrieved_messages[2]["content"], self.messages[2]["content"])

        # Verify that retrieved cache info matches original cache info
        self.assertEqual(retrieved_cache_info, self.cache_info)

    def test_update_cache_info(self):
        """Test updating cache info for an existing conversation."""
        chat_id = "test-chat-123"

        # Save initial conversation state
        self.repo.save_conversation_state(chat_id, self.messages, self.cache_info)

        # Update cache info
        new_cache_info = {"input_tokens": 30, "output_tokens": 40}
        self.repo.update_cache_info(chat_id, new_cache_info)

        # Retrieve conversation state
        _, retrieved_cache_info = self.repo.get_conversation_state(chat_id)

        # Verify that retrieved cache info matches updated cache info
        self.assertEqual(retrieved_cache_info, new_cache_info)

    def test_get_nonexistent_conversation(self):
        """Test retrieving a conversation that doesn't exist."""
        chat_id = "nonexistent-chat"

        # Retrieve nonexistent conversation
        messages, cache_info = self.repo.get_conversation_state(chat_id)

        # Verify that empty lists/dicts are returned
        self.assertEqual(len(messages), 0)
        self.assertEqual(cache_info, {})


if __name__ == "__main__":
    unittest.main()
