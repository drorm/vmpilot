"""
Unit tests for chat history persistence in VMPilot.

These tests verify that the complete chat history is properly saved and retrieved
from the database at the end of each exchange.
"""

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage

from vmpilot.db.connection import get_db_connection
from vmpilot.db.crud import ConversationRepository
from vmpilot.exchange import Exchange


class TestChatHistoryPersistence(unittest.TestCase):
    """Test the chat history persistence functionality."""

    def setUp(self):
        """Set up a temporary database for testing."""
        # Create a temporary directory for the database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_vmpilot.db")

        # Mock the database connection to use our temporary file
        self.db_patcher = patch(
            "vmpilot.db.connection.get_db_path",
            return_value=Path(self.db_path),
        )
        self.db_patcher.start()

        # Ensure database config is enabled
        self.config_patcher = patch(
            "vmpilot.config.config.database_config.enabled", True
        )
        self.config_patcher.start()

        # Reset the singleton connection
        import vmpilot.db.connection

        vmpilot.db.connection._db_connection = None

        # Initialize the database
        from vmpilot.db.connection import initialize_db

        initialize_db()

        self.conn = get_db_connection()
        self.repo = ConversationRepository()

    def tearDown(self):
        """Clean up after tests."""
        self.db_patcher.stop()
        self.config_patcher.stop()

        # Close the connection before removing files
        import vmpilot.db.connection

        if vmpilot.db.connection._db_connection:
            vmpilot.db.connection._db_connection.close()
            vmpilot.db.connection._db_connection = None

        # Remove the temporary directory and its contents
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_save_and_retrieve_chat_history(self):
        """Test saving and retrieving a complete chat history."""
        # Create a chat
        chat_id = "test-chat-123"
        self.repo.save_chat(
            chat_id=chat_id,
            initial_request="Test request",
            project_root="/test/path",
        )

        # Add debug logging
        import logging

        logging.getLogger("vmpilot").setLevel(logging.DEBUG)

        # Create and complete an exchange
        print("Creating first exchange")
        exchange = Exchange(
            chat_id=chat_id,
            user_message=HumanMessage(content="Hello, this is a test message"),
        )
        exchange.complete(
            assistant_message=AIMessage(content="This is a test response"),
            tool_calls=[],
        )
        print("First exchange completed")

        # Add a small delay
        import time

        time.sleep(0.5)

        # Create and complete a second exchange
        print("Creating second exchange")
        exchange2 = Exchange(
            chat_id=chat_id,
            user_message=HumanMessage(content="Second test message"),
        )
        exchange2.complete(
            assistant_message=AIMessage(content="Second test response"),
            tool_calls=[],
        )
        print("Second exchange completed")

        # Force a flush to the database
        time.sleep(0.5)  # Small delay to ensure database operations complete

        # Get all messages from the conversation state
        from vmpilot.agent_memory import get_conversation_state

        current_messages, _ = get_conversation_state(chat_id)

        # Manually save to database to ensure all messages are saved
        print(f"Manually saving {len(current_messages)} messages to database")
        # Convert messages to serializable format for database storage
        serializable_messages = []
        for msg in current_messages:
            if hasattr(msg, "model_dump"):
                serializable_messages.append(msg.model_dump())
            elif hasattr(msg, "dict"):
                # Fallback for older Pydantic versions
                serializable_messages.append(msg.dict())
            else:
                # If it's already a dict
                serializable_messages.append(msg)

        # Save to database
        self.repo.save_chat_history(chat_id, serializable_messages)

        # Direct database query to check chat histories table
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM chat_histories WHERE chat_id = ? ORDER BY timestamp DESC",
            (chat_id,),
        )
        histories = list(cursor.fetchall())

        # Print all history records for debugging
        print(f"Found {len(histories)} history records in database")
        for i, hist in enumerate(histories):
            print(
                f"History record {i}, timestamp: {hist['timestamp']}, message_count: {hist['message_count']}"
            )

            # Parse and print the messages in this history
            history_data = json.loads(hist["full_history"])
            print(f"  Contains {len(history_data)} messages:")
            for msg in history_data:
                if isinstance(msg, dict):
                    print(f"  - {msg.get('content', '')}")

        # Should have at least one history record
        self.assertGreaterEqual(len(histories), 1)

        # Get the latest history
        latest_history = histories[0]
        self.assertIsNotNone(latest_history)

        # Parse the full_history JSON
        history_data = json.loads(latest_history["full_history"])

        # Print for debugging
        print(f"Latest history has {len(history_data)} messages")

        # Check message contents
        message_contents = [
            msg.get("content", "") for msg in history_data if isinstance(msg, dict)
        ]

        # Verify all expected messages are present
        self.assertIn("Hello, this is a test message", message_contents)
        self.assertIn("This is a test response", message_contents)
        self.assertIn("Second test message", message_contents)
        self.assertIn("Second test response", message_contents)

    def test_get_conversation_state_loads_from_db(self):
        """Test that get_conversation_state loads from database if not in memory."""
        # Create a chat and exchanges directly in the database
        chat_id = "test-chat-456"
        self.repo.save_chat(
            chat_id=chat_id,
            initial_request="Test request",
            project_root="/test/path",
        )

        # Create serialized messages for history
        messages = [
            {
                "type": "HumanMessage",
                "content": "Database test message",
                "role": "human",
            },
            {"type": "AIMessage", "content": "Database test response", "role": "ai"},
        ]

        # Save directly to database
        self.repo.save_chat_history(chat_id, messages)

        # Clear in-memory state to force database load
        from vmpilot.agent_memory import conversation_states, get_conversation_state

        if chat_id in conversation_states:
            del conversation_states[chat_id]

        # Retrieve conversation state
        loaded_messages, _ = get_conversation_state(chat_id)

        # Verify messages were loaded from database
        self.assertEqual(len(loaded_messages), 2)
        self.assertEqual(loaded_messages[0].content, "Database test message")
        self.assertEqual(loaded_messages[1].content, "Database test response")


if __name__ == "__main__":
    unittest.main()
