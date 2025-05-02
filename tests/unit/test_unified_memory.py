"""
Unit tests for the unified memory module.

Tests that the unified_memory module correctly selects between
in-memory and database storage based on configuration.
"""

import unittest
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class TestUnifiedMemory(unittest.TestCase):
    """Test cases for the unified memory module."""

    def setUp(self):
        """Set up test environment."""
        # Create sample messages for testing
        self.messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Hello, how are you?"),
            AIMessage(content="I'm doing well, thank you for asking!"),
        ]

        # Sample cache info
        self.cache_info = {"input_tokens": 10, "output_tokens": 20}

        # Sample thread ID
        self.thread_id = "test-thread-123"

    def test_uses_agent_memory_when_db_disabled(self):
        """Test that agent_memory is used when database is disabled."""
        # Setup mocks
        mock_agent_memory = MagicMock()
        mock_persistent_memory = MagicMock()
        mock_config = MagicMock()
        mock_config.is_database_enabled.return_value = False

        # Patch the imports and config
        with patch.dict(
            "sys.modules",
            {
                "vmpilot.agent_memory": mock_agent_memory,
                "vmpilot.persistent_memory": mock_persistent_memory,
                "vmpilot.config": MagicMock(config=mock_config),
            },
        ):

            # Import the unified_memory module with our mocks in place
            from importlib import reload

            import vmpilot.unified_memory

            reload(vmpilot.unified_memory)

            # Call a function from the module
            vmpilot.unified_memory.save_conversation_state(
                self.thread_id, self.messages, self.cache_info
            )

            # Verify that agent_memory was used
            mock_agent_memory.save_conversation_state.assert_called_once_with(
                self.thread_id, self.messages, self.cache_info
            )

            # Verify that persistent_memory was not used
            mock_persistent_memory.save_conversation_state.assert_not_called()

    def test_uses_persistent_memory_when_db_enabled(self):
        """Test that persistent_memory is used when database is enabled."""
        # Setup mocks
        mock_agent_memory = MagicMock()
        mock_persistent_memory = MagicMock()
        mock_config = MagicMock()
        mock_config.is_database_enabled.return_value = True

        # Patch the imports and config
        with patch.dict(
            "sys.modules",
            {
                "vmpilot.agent_memory": mock_agent_memory,
                "vmpilot.persistent_memory": mock_persistent_memory,
                "vmpilot.config": MagicMock(config=mock_config),
            },
        ):

            # Import the unified_memory module with our mocks in place
            import sys
            from importlib import reload

            if "vmpilot.unified_memory" in sys.modules:
                del sys.modules["vmpilot.unified_memory"]
            import vmpilot.unified_memory

            reload(vmpilot.unified_memory)

            # Call a function from the module
            vmpilot.unified_memory.save_conversation_state(
                self.thread_id, self.messages, self.cache_info
            )

            # Verify that persistent_memory was used
            mock_persistent_memory.save_conversation_state.assert_called_once_with(
                self.thread_id, self.messages, self.cache_info
            )

            # Verify that agent_memory was not used
            mock_agent_memory.save_conversation_state.assert_not_called()


if __name__ == "__main__":
    unittest.main()
