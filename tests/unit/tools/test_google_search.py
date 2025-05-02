import os
from unittest.mock import MagicMock, patch

import pytest

from vmpilot.tools.google_search_tool import GoogleSearchTool


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
    def mock_wrapper(self):
        """Create a mock for GoogleSearchAPIWrapper"""
        with patch("vmpilot.tools.google_search_tool.GoogleSearchAPIWrapper") as mock:
            # Configure the mock to return a predefined list of results
            wrapper_instance = mock.return_value
            wrapper_instance.results.return_value = [
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
            yield mock

    def test_init_with_valid_env_vars(self, mock_env_vars, mock_wrapper):
        """Test initialization with valid environment variables"""
        tool = GoogleSearchTool()
        assert tool.is_configured is True
        assert tool.search is not None
        mock_wrapper.assert_called_once_with(
            google_api_key="test_api_key", google_cse_id="test_cse_id", k=10
        )

    def test_init_with_missing_env_vars(self, mock_missing_env_vars):
        """Test initialization with missing environment variables"""
        tool = GoogleSearchTool()
        assert tool.is_configured is False
        assert tool.search is None

    def test_run_with_valid_configuration(self, mock_env_vars, mock_wrapper):
        """Test successful search execution"""
        tool = GoogleSearchTool()
        result = tool._run("test query", num_results=2)

        # Verify the search was executed
        tool.search.results.assert_called_once_with("test query", 2)

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

    def test_run_with_empty_results(self, mock_env_vars, mock_wrapper):
        """Test search execution with empty results"""
        tool = GoogleSearchTool()
        tool.search.results.return_value = []

        result = tool._run("test query")
        assert "No results found for your query" in result

    def test_run_with_connection_error(self, mock_env_vars, mock_wrapper):
        """Test search execution with connection error"""
        tool = GoogleSearchTool()
        tool.search.results.side_effect = ConnectionError("Failed to connect")

        result = tool._run("test query")
        assert "Error: Could not connect to Google Search API" in result
        assert "Failed to connect" in result

    def test_run_with_value_error(self, mock_env_vars, mock_wrapper):
        """Test search execution with value error"""
        tool = GoogleSearchTool()
        tool.search.results.side_effect = ValueError("Invalid parameters")

        result = tool._run("test query")
        assert "Error: Invalid search parameters" in result
        assert "Invalid parameters" in result

    def test_run_with_unexpected_error(self, mock_env_vars, mock_wrapper):
        """Test search execution with unexpected error"""
        tool = GoogleSearchTool()
        tool.search.results.side_effect = Exception("Unexpected error")

        result = tool._run("test query")
        assert "Error performing search" in result
        assert "Unexpected error" in result
