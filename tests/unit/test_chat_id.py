import re
from unittest.mock import MagicMock

import pytest

from vmpilot.vmpilot import Pipeline


class TestChatID:
    @pytest.fixture
    def pipeline(self):
        """Create a fresh Pipeline instance for each test."""
        return Pipeline()

    @pytest.fixture
    def mock_callback(self):
        """Create a mock callback function for testing."""
        return MagicMock()

    def test_generate_new_chat_id(self, pipeline, mock_callback):
        """Test that a new chat_id is generated when none exists and messages are minimal."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
        ]

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # Verify chat_id format: 8 alphanumeric characters
        assert chat_id is not None
        assert len(chat_id) == 8
        assert re.match(r"^[a-zA-Z0-9]{8}$", chat_id)

        # Verify callback was called with the correct message
        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0][0]
        assert call_args["type"] == "text"
        assert f"Chat id :{chat_id}" in call_args["text"]

    def test_extract_existing_chat_id_from_messages(self, pipeline, mock_callback):
        """Test that an existing chat_id is extracted from previous messages."""
        test_chat_id = "abc12345"
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {
                "role": "assistant",
                "content": f"Chat id:{test_chat_id}\n\nAssistant response",
            },
        ]

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # Verify extracted chat_id
        assert chat_id == test_chat_id
        # Verify callback was not called
        mock_callback.assert_not_called()

    def test_use_existing_instance_chat_id(self, pipeline, mock_callback):
        """Test that a new chat_id is generated when there's no body chat_id."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
        ]

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # Verify a new chat_id is generated with correct format
        assert chat_id is not None
        assert len(chat_id) == 8
        assert re.match(r"^[a-zA-Z0-9]{8}$", chat_id)
        # Verify callback was called (in the new implementation, callback is always called)
        mock_callback.assert_called_once()

    def test_extract_chat_id_with_spaces(self, pipeline, mock_callback):
        """Test extracting chat_id with spaces in the format."""
        test_chat_id = "space123"
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {
                "role": "assistant",
                "content": f"Chat id: {test_chat_id} \n\nAssistant response",
            },
        ]

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # Verify extracted chat_id
        assert chat_id == test_chat_id
        # Verify callback was not called
        mock_callback.assert_not_called()

    def test_no_chat_id_in_messages(self, pipeline, mock_callback):
        """Test behavior when no chat_id is found in messages and there are more than 2 messages."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message 1"},
            {"role": "assistant", "content": "Assistant response without chat id"},
            {"role": "user", "content": "User message 2"},
        ]

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # In this case, since there are more than 2 messages but no chat_id,
        # we should still get None as the chat_id
        assert chat_id is None
        # Verify callback was not called
        mock_callback.assert_not_called()

    def test_empty_messages(self, pipeline, mock_callback):
        """Test behavior with empty messages list."""
        messages = []

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # Since messages is empty, it's considered a new conversation
        assert chat_id is not None
        assert len(chat_id) == 8
        # Verify callback was called
        mock_callback.assert_called_once()

    def test_non_string_content(self, pipeline, mock_callback):
        """Test behavior when assistant message has non-string content."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Chat id:abc12345\n\nResponse"}],
            },
        ]

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # Since content is not a string, chat_id should not be found
        assert chat_id is None
        # Verify callback was not called
        mock_callback.assert_not_called()

    def test_multiple_assistant_messages(self, pipeline, mock_callback):
        """Test behavior with multiple assistant messages, only first should be checked."""
        test_chat_id = "first123"
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message 1"},
            {
                "role": "assistant",
                "content": f"Chat id:{test_chat_id}\n\nFirst response",
            },
            {"role": "user", "content": "User message 2"},
            {"role": "assistant", "content": "Chat id:second456\n\nSecond response"},
        ]

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # Should extract chat_id from the first assistant message
        assert chat_id == test_chat_id
        # Verify callback was not called
        mock_callback.assert_not_called()

    def test_chat_id_priority(self, pipeline, mock_callback):
        """Test that chat_id from messages is extracted correctly."""
        extracted_chat_id = "extracted456"
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {
                "role": "assistant",
                "content": f"Chat id:{extracted_chat_id}\n\nAssistant response",
            },
        ]

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # Should extract the chat_id from messages
        assert chat_id == extracted_chat_id
        # Verify callback was not called
        mock_callback.assert_not_called()

    def test_malformed_chat_id_line(self, pipeline, mock_callback):
        """Test behavior with malformed chat_id line in assistant message."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {
                "role": "assistant",
                "content": "ChatId without proper formatting\n\nAssistant response",
            },
        ]

        chat_id = pipeline.get_or_generate_chat_id(messages, mock_callback)

        # Since chat_id line is malformed, no chat_id should be found
        assert chat_id is None
        # Verify callback was not called
        mock_callback.assert_not_called()
