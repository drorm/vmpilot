import os
from unittest.mock import patch

import pytest

from vmpilot.tools.google_search_tool import GoogleSearchTool
from vmpilot.tools.setup_tools import is_google_search_enabled, setup_tools


class TestSetupTools:
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

    def test_is_google_search_enabled_with_env_vars(self, mock_env_vars):
        """Test is_google_search_enabled with valid environment variables"""
        assert is_google_search_enabled() is True

    def test_is_google_search_enabled_without_env_vars(self, mock_missing_env_vars):
        """Test is_google_search_enabled with missing environment variables"""
        assert is_google_search_enabled() is False

    def test_is_google_search_enabled_with_partial_env_vars(self, monkeypatch):
        """Test is_google_search_enabled with partial environment variables"""
        # Only set API key
        monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key")
        monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)
        assert is_google_search_enabled() is False

        # Only set CSE ID
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_CSE_ID", "test_cse_id")
        assert is_google_search_enabled() is False

    @patch("vmpilot.tools.setup_tools.GoogleSearchTool")
    def test_setup_tools_with_google_search_enabled(
        self,
        mock_google_search,
        mock_env_vars,
    ):
        """Test setup_tools with Google Search enabled"""
        # Configure mock for GoogleSearchTool
        mock_google_search_instance = mock_google_search.return_value
        mock_google_search_instance.is_configured = True
        mock_google_search_instance.get_schema = lambda: {
            "name": "google_search",
            "description": "Search Google",
            "parameters": {},
        }
        mock_google_search_instance._run = lambda x: "mock result"

        # Call setup_tools (no llm parameter needed)
        tools = setup_tools()

        # Verify GoogleSearchTool was created
        mock_google_search.assert_called_once()

        # Verify number of tools (should be 4 including Google Search)
        assert len(tools) == 4

    @patch("vmpilot.tools.setup_tools.GoogleSearchTool")
    def test_setup_tools_with_google_search_not_configured(
        self,
        mock_google_search,
        mock_env_vars,
    ):
        """Test setup_tools with Google Search not properly configured"""
        # Configure mock for GoogleSearchTool
        mock_google_search_instance = mock_google_search.return_value
        mock_google_search_instance.is_configured = False

        # Call setup_tools (no llm parameter needed)
        tools = setup_tools()

        # Verify GoogleSearchTool was instantiated
        mock_google_search.assert_called_once()

        # Verify number of tools (should be 3, core tools only since Google Search is not configured)
        assert len(tools) == 3

    @patch("vmpilot.tools.setup_tools.is_google_search_enabled", return_value=False)
    def test_setup_tools_with_google_search_disabled(
        self,
        mock_is_enabled,
        mock_missing_env_vars,
    ):
        """Test setup_tools with Google Search disabled"""
        # Call setup_tools (no llm parameter needed)
        tools = setup_tools()

        # Verify is_google_search_enabled was called
        mock_is_enabled.assert_called_once()

        # Verify number of tools (should be 3, core tools only)
        assert len(tools) == 3

    def test_setup_tools_with_no_llm(self):
        """Test setup_tools with no LLM provided"""
        tools = setup_tools()
        # Should still work and return core tools (3) plus Google Search if enabled (depends on env)
        assert len(tools) >= 3
