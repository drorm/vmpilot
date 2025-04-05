import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, "/home/dror/vmpilot")
from vmpilot.chat import Chat


class TestChatDirectoryErrors:
    """Tests for the directory error handling in Chat class."""

    @pytest.fixture
    def mock_callback(self):
        """Create a mock callback function."""
        return MagicMock()

    @pytest.fixture
    def default_messages(self):
        """Default messages for testing."""
        return [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
        ]

    @patch("os.path.exists")
    @patch("os.chdir")
    def test_nonexistent_directory_raises_exception(
        self, mock_chdir, mock_exists, mock_callback, default_messages
    ):
        """Test that a non-existent project directory raises Exception."""
        # Setup mock to indicate directory doesn't exist
        mock_exists.return_value = False

        # Test that creating a Chat with non-existent directory raises Exception
        with pytest.raises(Exception) as excinfo:
            chat = Chat(
                messages=default_messages,
                output_callback=mock_callback,
                system_prompt_suffix="$PROJECT_ROOT=/nonexistent/directory",
            )
            chat.chat_id = "test123"  # Set chat_id after initialization

        # Verify the exception message contains useful information
        assert "does not exist" in str(excinfo.value)
        assert "https://vmpdocs" in str(excinfo.value)  # Check for documentation link

        # Verify os.chdir was not called
        mock_chdir.assert_not_called()

    @patch("os.path.exists")
    @patch("os.chdir")
    @patch("os.path.isdir")
    def test_permission_error_during_chdir(
        self, mock_isdir, mock_chdir, mock_exists, mock_callback, default_messages
    ):
        """Test that permission errors during directory change are properly handled."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_chdir.side_effect = PermissionError("Permission denied")

        # Test that permission error is caught and re-raised with context
        with pytest.raises(Exception) as excinfo:
            chat = Chat(
                messages=default_messages,
                output_callback=mock_callback,
                system_prompt_suffix="$PROJECT_ROOT=/protected/directory",
            )
            chat.chat_id = "test123"  # Set chat_id after initialization

        # Verify the exception message contains useful information
        expected_msg = "Failed to change to project directory /protected/directory: Permission denied"
        assert expected_msg == str(excinfo.value)

        # Verify os.chdir was called
        mock_chdir.assert_called_once()

    @patch("vmpilot.env.os.path.exists")
    @patch("vmpilot.env.os.chdir")
    @patch("vmpilot.env.os.path.isdir")
    def test_successful_directory_change(
        self, mock_isdir, mock_chdir, mock_exists, mock_callback, default_messages
    ):
        """Test successful directory change when directory exists."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = True

        # Create Chat instance
        chat = Chat(
            messages=default_messages,
            output_callback=mock_callback,
            system_prompt_suffix="$PROJECT_ROOT=/valid/directory",
        )
        chat.chat_id = "test123"  # Set chat_id after initialization

        # Verify os.chdir was called with the expanded path
        assert mock_chdir.call_count >= 1
        args, _ = mock_chdir.call_args
        assert args[0] == os.path.expanduser("/valid/directory")

    @patch("vmpilot.env.os.path.exists")
    @patch("vmpilot.env.os.chdir")
    @patch("vmpilot.env.os.path.isdir")
    def test_tilde_expansion_in_project_dir(
        self, mock_isdir, mock_chdir, mock_exists, mock_callback, default_messages
    ):
        """Test that tilde in project directory path is properly expanded."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = True

        # Create Chat instance with tilde in path
        chat = Chat(
            messages=default_messages,
            output_callback=mock_callback,
            system_prompt_suffix="$PROJECT_ROOT=~/my_project",
        )
        chat.chat_id = "test123"  # Set chat_id after initialization

        # Verify os.chdir was called with the expanded path
        assert mock_chdir.call_count >= 1
        args, _ = mock_chdir.call_args
        assert args[0] == os.path.expanduser("~/my_project")

    @patch("os.path.exists")
    @patch("os.chdir")
    @patch("os.path.isdir")
    def test_not_a_directory_error(
        self, mock_isdir, mock_chdir, mock_exists, mock_callback, default_messages
    ):
        """Test error handling when path exists but is not a directory."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = False

        # Test that error is properly raised
        with pytest.raises(Exception) as excinfo:
            chat = Chat(
                messages=default_messages,
                output_callback=mock_callback,
                system_prompt_suffix="$PROJECT_ROOT=/path/to/file.txt",  # This is a file, not a directory
            )
            chat.chat_id = "test123"  # Set chat_id after initialization

        # Verify the exception message contains useful information
        expected_msg = (
            "Failed to change to project directory /path/to/file.txt: Not a directory"
        )
        assert expected_msg == str(excinfo.value)

        # Verify os.chdir was not called since isdir check happens first
        mock_chdir.assert_not_called()
