import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, "/home/dror/vmpilot")
from vmpilot.vmpilot import Pipeline
from vmpilot.chat import DirException


class TestPipelineErrorHandling:
    """Tests for error handling in the Pipeline class."""
    
    @pytest.fixture
    def pipeline(self):
        """Create a fresh Pipeline instance for each test."""
        return Pipeline()
    
    @pytest.fixture
    def default_messages(self):
        """Default messages for testing."""
        return [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"}
        ]
    
    @patch('vmpilot.chat.Chat')
    def test_directory_error_handling_in_pipeline(self, mock_chat, pipeline, default_messages):
        """Test that Pipeline properly handles directory exceptions from Chat."""
        # Setup mock to raise DirException
        error_message = "Project directory /nonexistent/dir does not exist. See https://vmpdocs..."
        mock_chat.side_effect = DirException(error_message)
        
        # Create a generator from the process method
        generator = pipeline.process({"messages": default_messages})
        
        # Get the first yielded value (should be the error message)
        response = next(generator)
        
        # Verify the error message is returned
        assert error_message in response
        
        # Verify no further values are yielded
        with pytest.raises(StopIteration):
            next(generator)
    
    @patch('vmpilot.chat.Chat')
    def test_generic_exception_handling_in_pipeline(self, mock_chat, pipeline, default_messages):
        """Test that Pipeline properly handles generic exceptions from Chat."""
        # Setup mock to raise a generic Exception
        error_message = "Some unexpected error occurred"
        mock_chat.side_effect = Exception(error_message)
        
        # Create a generator from the process method
        generator = pipeline.process({"messages": default_messages})
        
        # Get the first yielded value (should be the error message)
        response = next(generator)
        
        # Verify the error message is returned
        assert error_message in response
        
        # Verify no further values are yielded
        with pytest.raises(StopIteration):
            next(generator)
    
    @patch('vmpilot.chat.Chat')
    @patch('threading.Thread')
    def test_successful_chat_creation_continues_processing(self, mock_thread, mock_chat, pipeline, default_messages):
        """Test that pipeline continues processing when Chat creation is successful."""
        # Setup mock to return a valid Chat instance
        mock_chat_instance = MagicMock()
        mock_chat_instance.chat_id = "test123"
        mock_chat.return_value = mock_chat_instance
        
        # Setup mock thread to do nothing (prevent actual processing)
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Call the process method
        list(pipeline.process({"messages": default_messages}))
        
        # Verify that the thread was started (indicating processing continued)
        mock_thread_instance.start.assert_called_once()
    
    @patch('vmpilot.chat.Chat')
    def test_error_in_sampling_loop(self, mock_chat, pipeline, default_messages):
        """Test that errors in the sampling loop are properly handled."""
        # Setup a mock Chat instance
        mock_chat_instance = MagicMock()
        mock_chat_instance.chat_id = "test123"
        mock_chat.return_value = mock_chat_instance
        
        # Set up the sampling_loop to raise an exception
        def mock_run(*args, **kwargs):
            raise Exception("Error in sampling loop")
            
        with patch.object(pipeline, '_run_sampling_loop', side_effect=mock_run):
            # Process the messages
            list(pipeline.process({"messages": default_messages}))
            
            # No assertion needed - test passes if no unhandled exception is raised