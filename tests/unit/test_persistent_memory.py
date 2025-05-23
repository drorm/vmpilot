"""
Unit tests for the persistent_memory module.

Tests the functionality of the persistent conversation state manager
which provides the same interface as agent_memory but uses SQLite.
"""

import sqlite3
import unittest
from unittest.mock import MagicMock, patch

from vmpilot.db.crud import ConversationRepository
from vmpilot.persistent_memory import (
    clear_conversation_state,
    get_conversation_state,
    save_conversation_state,
    update_cache_info,
)


class TestPersistentMemory(unittest.TestCase):
    """Test cases for persistent_memory module."""

    def setUp(self):
        """Set up test environment."""
        # Create sample messages for testing
        self.messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
        ]

        # Sample cache info
        self.cache_info = {"input_tokens": 10, "output_tokens": 20}

        # Sample thread ID
        self.thread_id = "test-thread-123"

        # Create a mock repository
        self.mock_repo = MagicMock(spec=ConversationRepository)

        # Patch the repository in persistent_memory
        self.repo_patcher = patch("vmpilot.persistent_memory._repo", self.mock_repo)
        self.repo_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        # Stop the patcher
        self.repo_patcher.stop()

    def test_save_conversation_state(self):
        """Test that save_conversation_state calls the repository correctly."""
        # Configure mock to return empty state
        self.mock_repo.get_conversation_state.return_value = ([], {})

        # Call the function under test
        save_conversation_state(self.thread_id, self.messages, self.cache_info)

        # Verify that the repository was called correctly
        self.mock_repo.save_conversation_state.assert_called_once_with(
            self.thread_id, self.messages, self.cache_info
        )

    def test_save_conversation_state_with_no_cache_info(self):
        """Test save_conversation_state with no cache_info parameter."""
        # Configure mock to return existing cache info
        existing_cache_info = {"input_tokens": 5, "output_tokens": 15}
        self.mock_repo.get_conversation_state.return_value = ([], existing_cache_info)

        # Call the function under test without cache_info
        save_conversation_state(self.thread_id, self.messages)

        # Verify that the repository was called with existing cache info
        self.mock_repo.save_conversation_state.assert_called_once_with(
            self.thread_id, self.messages, existing_cache_info
        )

    def test_get_conversation_state(self):
        """Test that get_conversation_state returns repository results."""
        # Configure mock to return specific values
        self.mock_repo.get_conversation_state.return_value = (
            self.messages,
            self.cache_info,
        )

        # Call the function under test
        messages, cache_info = get_conversation_state(self.thread_id)

        # Verify that the repository was called correctly
        self.mock_repo.get_conversation_state.assert_called_once_with(self.thread_id)

        # Verify that the returned values match what the repository returned
        self.assertEqual(messages, self.messages)
        self.assertEqual(cache_info, self.cache_info)

    def test_update_cache_info(self):
        """Test that update_cache_info calls the repository correctly."""
        # Call the function under test
        update_cache_info(self.thread_id, self.cache_info)

        # Verify that the repository was called correctly
        self.mock_repo.update_cache_info.assert_called_once_with(
            self.thread_id, self.cache_info
        )

    def test_clear_conversation_state(self):
        """Test that clear_conversation_state calls the repository correctly."""
        # Call the function under test
        clear_conversation_state(self.thread_id)

        # Verify that the repository was called correctly
        self.mock_repo.clear_conversation_state.assert_called_once_with(self.thread_id)


if __name__ == "__main__":
    unittest.main()
