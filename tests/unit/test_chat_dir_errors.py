import os
import pytest
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, "/home/dror/vmpilot")
from vmpilot.chat import Chat, DirException


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
            {"role": "user", "content": "User message"}
        ]
    
    @patch('os.path.exists')
    @patch('os.chdir')
    def test_nonexistent_directory_raises_exception(self, mock_chdir, mock_exists, mock_callback, default_messages):
        """Test that a non-existent project directory raises DirException."""
        # Setup mock to indicate directory doesn't exist
        mock_exists.return_value = False
        
        # Test that creating a Chat with non-existent directory raises DirException
        with pytest.raises(DirException) as excinfo:
            Chat(
                chat_id="test123",
                messages=default_messages,
                output_callback=mock_callback,
                project_dir="/nonexistent/directory"
            )
        
        # Verify the exception message contains useful information
        assert "does not exist" in str(excinfo.value)
        assert "https://vmpdocs" in str(excinfo.value)  # Check for documentation link
        
        # Verify os.chdir was not called
        mock_chdir.assert_not_called()
    
    @patch('os.path.exists')
    @patch('os.chdir')
    @patch('os.path.isdir')
    def test_permission_error_during_chdir(self, mock_isdir, mock_chdir, mock_exists, mock_callback, default_messages):
        """Test that permission errors during directory change are properly handled."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_chdir.side_effect = PermissionError("Permission denied")
        
        # Test that permission error is caught and re-raised with context
        with pytest.raises(Exception) as excinfo:
            Chat(
                chat_id="test123",
                messages=default_messages,
                output_callback=mock_callback,
                project_dir="/protected/directory"
            )
        
        # Verify the exception message contains useful information
        expected_msg = "Failed to change to project directory /protected/directory: Permission denied"
        assert expected_msg == str(excinfo.value)
        
        # Verify os.chdir was called
        mock_chdir.assert_called_once()
    
    @patch('os.path.exists')
    @patch('os.chdir')
    @patch('os.path.isdir')
    def test_successful_directory_change(self, mock_isdir, mock_chdir, mock_exists, mock_callback, default_messages):
        """Test successful directory change when directory exists."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        # Create Chat instance
        chat = Chat(
            chat_id="test123",
            messages=default_messages,
            output_callback=mock_callback,
            project_dir="/valid/directory"
        )
        
        # Verify os.chdir was called with the expanded path
        mock_chdir.assert_called_once()
        args, _ = mock_chdir.call_args
        assert args[0] == os.path.expanduser("/valid/directory")
    
    @patch('os.path.exists')
    @patch('os.chdir')
    @patch('os.path.isdir')
    def test_tilde_expansion_in_project_dir(self, mock_isdir, mock_chdir, mock_exists, mock_callback, default_messages):
        """Test that tilde in project directory path is properly expanded."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        # Create Chat instance with tilde in path
        chat = Chat(
            chat_id="test123",
            messages=default_messages,
            output_callback=mock_callback,
            project_dir="~/my_project"
        )
        
        # Verify os.chdir was called with the expanded path
        mock_chdir.assert_called_once()
        args, _ = mock_chdir.call_args
        assert args[0] == os.path.expanduser("~/my_project")
    
    @patch('os.path.exists')
    @patch('os.chdir')
    @patch('os.path.isdir')
    def test_not_a_directory_error(self, mock_isdir, mock_chdir, mock_exists, mock_callback, default_messages):
        """Test error handling when path exists but is not a directory."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = False
        
        # Test that error is properly raised
        with pytest.raises(Exception) as excinfo:
            Chat(
                chat_id="test123",
                messages=default_messages,
                output_callback=mock_callback,
                project_dir="/path/to/file.txt"  # This is a file, not a directory
            )
        
        # Verify the exception message contains useful information
        expected_msg = "Failed to change to project directory /path/to/file.txt: Not a directory"
        assert expected_msg == str(excinfo.value)
        
        # Verify os.chdir was not called since isdir check happens first
        mock_chdir.assert_not_called()
