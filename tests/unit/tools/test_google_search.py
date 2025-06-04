import os
from unittest.mock import MagicMock, patch

import pytest

from vmpilot.tools.google_search_tool import GoogleSearchTool, google_search_executor


class TestGoogleSearchTool:
    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set mock environment variables for testing"""
        monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key")
        monkeypatch.setenv("GOOGLE_CSE_ID", "test_cse_id")

    @pytest.fixture
    def mock_missing_env_vars(self, monkeypatch):
        """Remove environment variables for testing missing configuration"""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)

    @pytest.fixture
    def mock_requests(self):
        """Create a mock for requests.get"""
        with patch("vmpilot.tools.google_search_tool.requests.get") as mock:
            # Configure the mock to return a predefined response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "items": [
                    {
                        "title": "Test Result 1",
                        "link": "https://example.com/1",
                        "snippet": "This is test snippet 1",
                    },
                    {
                        "title": "Test Result 2",
                        "link": "https://example.com/2",
                        "snippet": "This is test snippet 2",
                    },
                ]
            }
            mock.return_value = mock_response
            yield mock

    def test_init_with_valid_env_vars(self, mock_env_vars):
        """Test initialization with valid environment variables"""
        tool = GoogleSearchTool()
        assert tool.is_configured is True
        assert tool.google_api_key == "test_api_key"
        assert tool.google_cse_id == "test_cse_id"

    def test_init_with_missing_env_vars(self, mock_missing_env_vars):
        """Test initialization with missing environment variables"""
        tool = GoogleSearchTool()
        assert tool.is_configured is False

    def test_run_with_valid_configuration(self, mock_env_vars, mock_requests):
        """Test successful search execution"""
        tool = GoogleSearchTool()
        result = tool._run("test query", num_results=2)

        # Verify the API was called with correct parameters
        mock_requests.assert_called_once()
        call_args = mock_requests.call_args
        assert call_args[0][0] == "https://www.googleapis.com/customsearch/v1"
        params = call_args[1]["params"]
        assert params["key"] == "test_api_key"
        assert params["cx"] == "test_cse_id"
        assert params["q"] == "test query"
        assert params["num"] == 2

        # Check that the result contains expected formatted output
        assert "**Test Result 1**" in result
        assert "https://example.com/1" in result
        assert "This is test snippet 1" in result
        assert "**Test Result 2**" in result
        assert "https://example.com/2" in result
        assert "This is test snippet 2" in result

    def test_run_with_invalid_configuration(self, mock_missing_env_vars):
        """Test search execution with invalid configuration"""
        tool = GoogleSearchTool()
        result = tool._run("test query")

        assert "Google Search API is not properly configured" in result
        assert "GOOGLE_API_KEY" in result
        assert "GOOGLE_CSE_ID" in result

    def test_run_with_empty_results(self, mock_env_vars, mock_requests):
        """Test search execution with empty results"""
        tool = GoogleSearchTool()

        # Mock empty response
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_requests.return_value = mock_response

        result = tool._run("test query")
        assert "No results found for your query" in result

    def test_run_with_connection_error(self, mock_env_vars, mock_requests):
        """Test search execution with connection error"""
        import requests

        tool = GoogleSearchTool()
        mock_requests.side_effect = requests.ConnectionError("Failed to connect")

        result = tool._run("test query")
        assert "Error: Could not connect to Google Search API" in result
        assert "Failed to connect" in result

    def test_run_with_value_error(self, mock_env_vars, mock_requests):
        """Test search execution with value error"""
        tool = GoogleSearchTool()
        mock_requests.side_effect = ValueError("Invalid parameters")

        result = tool._run("test query")
        assert "Error: Invalid search parameters" in result
        assert "Invalid parameters" in result

    def test_run_with_unexpected_error(self, mock_env_vars, mock_requests):
        """Test search execution with unexpected error"""
        tool = GoogleSearchTool()
        mock_requests.side_effect = Exception("Unexpected error")

        result = tool._run("test query")
        assert "Error performing search" in result
        assert "Unexpected error" in result


class TestGoogleSearchExecutor:
    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set mock environment variables for testing"""
        monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key")
        monkeypatch.setenv("GOOGLE_CSE_ID", "test_cse_id")

    @pytest.fixture
    def mock_missing_env_vars(self, monkeypatch):
        """Remove environment variables for testing missing configuration"""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)

    @pytest.fixture
    def mock_requests(self):
        """Create a mock for requests.get"""
        with patch("vmpilot.tools.google_search_tool.requests.get") as mock:
            # Configure the mock to return a predefined response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "items": [
                    {
                        "title": "Test Result 1",
                        "link": "https://example.com/1",
                        "snippet": "This is test snippet 1",
                    },
                    {
                        "title": "Test Result 2",
                        "link": "https://example.com/2",
                        "snippet": "This is test snippet 2",
                    },
                ]
            }
            mock.return_value = mock_response
            yield mock

    def test_executor_with_valid_args(self, mock_env_vars, mock_requests):
        """Test google_search_executor with valid arguments"""
        args = {"query": "test query", "num_results": 2}
        result = google_search_executor(args)

        # Verify the API was called with correct parameters
        mock_requests.assert_called_once()
        call_args = mock_requests.call_args
        assert call_args[0][0] == "https://www.googleapis.com/customsearch/v1"
        params = call_args[1]["params"]
        assert params["key"] == "test_api_key"
        assert params["cx"] == "test_cse_id"
        assert params["q"] == "test query"
        assert params["num"] == 2

        # Check that the result contains expected formatted output
        assert "**Test Result 1**" in result
        assert "https://example.com/1" in result
        assert "This is test snippet 1" in result
        assert "**Test Result 2**" in result
        assert "https://example.com/2" in result
        assert "This is test snippet 2" in result

    def test_executor_with_default_num_results(self, mock_env_vars, mock_requests):
        """Test google_search_executor with default num_results"""
        args = {"query": "test query"}
        result = google_search_executor(args)

        # Verify the API was called with default num_results (10)
        mock_requests.assert_called_once()
        call_args = mock_requests.call_args
        params = call_args[1]["params"]
        assert params["num"] == 10

        # Check that the result contains expected formatted output
        assert "**Test Result 1**" in result

    def test_executor_with_missing_query(self):
        """Test google_search_executor with missing query parameter"""
        args = {"num_results": 5}
        result = google_search_executor(args)
        assert result == "Error: No search query provided"

    def test_executor_with_empty_query(self):
        """Test google_search_executor with empty query"""
        args = {"query": "", "num_results": 5}
        result = google_search_executor(args)
        assert result == "Error: No search query provided"

    def test_executor_with_none_query(self):
        """Test google_search_executor with None query"""
        args = {"query": None, "num_results": 5}
        result = google_search_executor(args)
        assert result == "Error: No search query provided"

    def test_executor_with_empty_args(self):
        """Test google_search_executor with empty args dictionary"""
        args = {}
        result = google_search_executor(args)
        assert result == "Error: No search query provided"

    def test_executor_with_invalid_configuration(self, mock_missing_env_vars):
        """Test google_search_executor with invalid configuration"""
        args = {"query": "test query"}
        result = google_search_executor(args)

        assert "Google Search API is not properly configured" in result
        assert "GOOGLE_API_KEY" in result
        assert "GOOGLE_CSE_ID" in result

    def test_executor_with_connection_error(self, mock_env_vars, mock_requests):
        """Test google_search_executor with connection error"""
        import requests

        args = {"query": "test query"}
        mock_requests.side_effect = requests.ConnectionError("Failed to connect")

        result = google_search_executor(args)
        assert "Error: Could not connect to Google Search API" in result
        assert "Failed to connect" in result

    def test_executor_with_value_error(self, mock_env_vars, mock_requests):
        """Test google_search_executor with value error"""
        args = {"query": "test query"}
        mock_requests.side_effect = ValueError("Invalid parameters")

        result = google_search_executor(args)
        assert "Error: Invalid search parameters" in result
        assert "Invalid parameters" in result

    def test_executor_with_unexpected_error(self, mock_env_vars, mock_requests):
        """Test google_search_executor with unexpected error"""
        args = {"query": "test query"}
        mock_requests.side_effect = Exception("Unexpected error")

        result = google_search_executor(args)
        assert "Error performing search" in result
        assert "Unexpected error" in result

    def test_executor_consistency_with_tool_run(self, mock_env_vars, mock_requests):
        """Test that google_search_executor returns same results as GoogleSearchTool._run"""
        args = {"query": "test query", "num_results": 2}

        # Get result from executor
        executor_result = google_search_executor(args)

        # Reset mock for second call
        mock_requests.reset_mock()

        # Configure the same mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/1",
                    "snippet": "This is test snippet 1",
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example.com/2",
                    "snippet": "This is test snippet 2",
                },
            ]
        }
        mock_requests.return_value = mock_response

        # Get result from tool
        tool = GoogleSearchTool()
        tool_result = tool._run("test query", num_results=2)

        # Results should be identical
        assert executor_result == tool_result

    def test_executor_with_extra_args(self, mock_env_vars, mock_requests):
        """Test google_search_executor ignores extra arguments"""
        args = {
            "query": "test query",
            "num_results": 2,
            "extra_param": "should_be_ignored",
            "another_param": 123,
        }
        result = google_search_executor(args)

        # Should work normally and ignore extra parameters
        assert "**Test Result 1**" in result
        assert "https://example.com/1" in result
