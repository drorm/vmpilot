"""
Unit tests for the ConversationRepository class using a fresh in-memory database.
"""

import json
import os
import sqlite3
import unittest
from unittest.mock import patch

from vmpilot.db.crud import ConversationRepository
from vmpilot.db.models import CREATE_TABLES_SQL


class TestRepository(unittest.TestCase):
    """Test the ConversationRepository with a completely isolated in-memory database."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class with module-level patches."""
        # Create a class-level patcher for the database connection
        cls.patcher = patch("vmpilot.db.crud.get_db_connection")

    def setUp(self):
        """Set up a fresh in-memory database for each test."""
        # Start the patcher
        self.mock_get_connection = self.patcher.start()

        # Create a new in-memory database for this test
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row

        # Initialize the database schema
        for statement in CREATE_TABLES_SQL:
            self.conn.execute(statement)
        self.conn.commit()

        # Make the mocked function return our in-memory connection
        self.mock_get_connection.return_value = self.conn

        # Create a repository instance using our mocked connection
        self.repo = ConversationRepository()

    def tearDown(self):
        """Clean up after each test."""
        # Close the database connection
        if hasattr(self, "conn"):
            self.conn.close()

        # Stop the patcher
        self.patcher.stop()

    def test_save_and_get_conversation(self):
        """Test saving and retrieving a conversation."""
        # Create test data
        conversation_id = "test-conversation-1"
        metadata = {"title": "Test Conversation", "tags": ["test"]}

        # Save the conversation
        result = self.repo.save_conversation(conversation_id, metadata)
        self.assertTrue(result, "Failed to save conversation")

        # Retrieve the conversation
        conversation = self.repo.get_conversation(conversation_id)

        # Verify the data
        self.assertIsNotNone(conversation, "Failed to retrieve conversation")
        self.assertEqual(conversation["id"], conversation_id)
        self.assertEqual(conversation["metadata"]["title"], "Test Conversation")
        self.assertEqual(conversation["metadata"]["tags"], ["test"])

    def test_save_and_get_message(self):
        """Test saving and retrieving a message."""
        # Create a conversation first
        conversation_id = "test-conversation-2"
        self.repo.save_conversation(conversation_id)

        # Save a message
        message_id = self.repo.save_message(
            conversation_id=conversation_id,
            role="user",
            content="Hello, world!",
            message_id="msg-123",
            metadata={"is_cached": False},
        )

        # Verify the save was successful
        self.assertIsNotNone(message_id, "Failed to save message")

        # Retrieve messages
        messages = self.repo.get_messages(conversation_id)

        # Verify message data
        self.assertEqual(len(messages), 1, "Wrong number of messages retrieved")
        message = messages[0]
        self.assertEqual(message["conversation_id"], conversation_id)
        self.assertEqual(message["role"], "user")
        self.assertEqual(message["content"], "Hello, world!")
        self.assertEqual(message["message_id"], "msg-123")
        self.assertEqual(message["metadata"]["is_cached"], False)

    def test_multiple_messages(self):
        """Test adding multiple messages to a conversation."""
        # Create a conversation
        conversation_id = "multi-message-conv"
        self.repo.save_conversation(conversation_id)

        # Add multiple messages
        self.repo.save_message(conversation_id, "user", "Hello")
        self.repo.save_message(conversation_id, "assistant", "Hi there!")
        self.repo.save_message(conversation_id, "user", "How are you?")
        self.repo.save_message(conversation_id, "assistant", "I'm doing well, thanks!")

        # Retrieve the messages
        messages = self.repo.get_messages(conversation_id)

        # Verify message count
        self.assertEqual(len(messages), 4, "Wrong number of messages retrieved")

        # Verify message order and content
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"], "Hi there!")
        self.assertEqual(messages[2]["role"], "user")
        self.assertEqual(messages[2]["content"], "How are you?")
        self.assertEqual(messages[3]["role"], "assistant")
        self.assertEqual(messages[3]["content"], "I'm doing well, thanks!")

    def test_get_all_conversations(self):
        """Test retrieving all conversations."""
        # Create multiple conversations
        self.repo.save_conversation("conv-1", {"title": "First Conversation"})
        self.repo.save_conversation("conv-2", {"title": "Second Conversation"})
        self.repo.save_conversation("conv-3", {"title": "Third Conversation"})

        # Retrieve all conversations
        conversations = self.repo.get_all_conversations()

        # Verify count
        self.assertEqual(
            len(conversations), 3, "Wrong number of conversations retrieved"
        )

        # Verify IDs are present
        conversation_ids = [conv["id"] for conv in conversations]
        self.assertIn("conv-1", conversation_ids)
        self.assertIn("conv-2", conversation_ids)
        self.assertIn("conv-3", conversation_ids)

    def test_delete_conversation(self):
        """Test deleting a conversation."""
        # Create a conversation with messages
        conversation_id = "delete-me"
        self.repo.save_conversation(conversation_id)
        self.repo.save_message(conversation_id, "user", "Delete this message")
        self.repo.save_message(conversation_id, "assistant", "Will be deleted")

        # Verify it exists
        self.assertIsNotNone(self.repo.get_conversation(conversation_id))
        self.assertEqual(len(self.repo.get_messages(conversation_id)), 2)

        # Delete the conversation
        result = self.repo.delete_conversation(conversation_id)
        self.assertTrue(result, "Failed to delete conversation")

        # Verify it's gone
        self.assertIsNone(self.repo.get_conversation(conversation_id))
        self.assertEqual(len(self.repo.get_messages(conversation_id)), 0)


if __name__ == "__main__":
    unittest.main()
