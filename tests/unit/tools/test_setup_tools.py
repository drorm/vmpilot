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

    @patch("vmpilot.tools.setup_tools.SetupShellTool")
    @patch("vmpilot.tools.setup_tools.EditTool")
    @patch("vmpilot.tools.setup_tools.CreateFileTool")
    @patch("vmpilot.tools.setup_tools.GoogleSearchTool")
    def test_setup_tools_with_google_search_enabled(
        self,
        mock_google_search,
        mock_create_file,
        mock_edit_tool,
        mock_shell_tool,
        mock_env_vars,
    ):
        """Test setup_tools with Google Search enabled"""
        # Configure mock for GoogleSearchTool
        mock_google_search_instance = mock_google_search.return_value
        mock_google_search_instance.is_configured = True

        # Call setup_tools with a mock LLM
        mock_llm = object()
        tools = setup_tools(llm=mock_llm)

        # Verify all tools were created
        mock_shell_tool.assert_called_once()
        mock_edit_tool.assert_called_once()
        mock_create_file.assert_called_once()
        mock_google_search.assert_called_once()

        # Verify number of tools (should be 4 including Google Search)
        assert len(tools) == 4

    @patch("vmpilot.tools.setup_tools.SetupShellTool")
    @patch("vmpilot.tools.setup_tools.EditTool")
    @patch("vmpilot.tools.setup_tools.CreateFileTool")
    @patch("vmpilot.tools.setup_tools.GoogleSearchTool")
    def test_setup_tools_with_google_search_not_configured(
        self,
        mock_google_search,
        mock_create_file,
        mock_edit_tool,
        mock_shell_tool,
        mock_env_vars,
    ):
        """Test setup_tools with Google Search not properly configured"""
        # Configure mock for GoogleSearchTool
        mock_google_search_instance = mock_google_search.return_value
        mock_google_search_instance.is_configured = False

        # Call setup_tools with a mock LLM
        mock_llm = object()
        tools = setup_tools(llm=mock_llm)

        # Verify all tool classes were instantiated
        mock_shell_tool.assert_called_once()
        mock_edit_tool.assert_called_once()
        mock_create_file.assert_called_once()
        mock_google_search.assert_called_once()

        # Verify number of tools (should be 4, core tools + Google Search even if not configured)
        assert len(tools) == 4

    @patch("vmpilot.tools.setup_tools.SetupShellTool")
    @patch("vmpilot.tools.setup_tools.EditTool")
    @patch("vmpilot.tools.setup_tools.CreateFileTool")
    @patch("vmpilot.tools.setup_tools.is_google_search_enabled", return_value=False)
    def test_setup_tools_with_google_search_disabled(
        self,
        mock_is_enabled,
        mock_create_file,
        mock_edit_tool,
        mock_shell_tool,
        mock_missing_env_vars,
    ):
        """Test setup_tools with Google Search disabled"""
        # Call setup_tools with a mock LLM
        mock_llm = object()
        tools = setup_tools(llm=mock_llm)

        # Verify core tools were created
        mock_shell_tool.assert_called_once()
        mock_edit_tool.assert_called_once()
        mock_create_file.assert_called_once()

        # Verify is_google_search_enabled was called
        mock_is_enabled.assert_called_once()

        # Verify number of tools (should be 3, core tools only)
        assert len(tools) == 3

    def test_setup_tools_with_no_llm(self):
        """Test setup_tools with no LLM provided"""
        tools = setup_tools(llm=None)
        assert len(tools) == 4
