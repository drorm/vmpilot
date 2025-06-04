import os
from unittest.mock import patch

import pytest

from vmpilot.tools.google_search_tool import GoogleSearchTool
from vmpilot.tools.setup_tools import (
    is_claude_model,
    is_gemini_model,
    is_google_search_enabled,
    setup_tools,
)


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

    def test_is_claude_model(self):
        """Test Claude model detection"""
        # Test Claude models
        assert is_claude_model("claude-3-5-sonnet-20241022") is True
        assert is_claude_model("claude-3-haiku-20240307") is True
        assert is_claude_model("claude-3-opus-20240229") is True
        assert is_claude_model("anthropic/claude-3-5-sonnet-20241022") is True

        # Test non-Claude models
        assert is_claude_model("gpt-4o") is False
        assert is_claude_model("gpt-3.5-turbo") is False
        assert is_claude_model("gemini-pro") is False

        # Test edge cases
        assert is_claude_model("") is False
        assert is_claude_model(None) is False

    def test_setup_tools_with_claude_model(self):
        """Test setup_tools with Claude model includes web search tool"""
        tools = setup_tools(model="claude-3-5-sonnet-20241022")

        # Find Claude search tool
        claude_search_found = False
        for tool in tools:
            schema = tool.get("schema", {})
            if (
                schema.get("type") == "web_search_20250305"
                and schema.get("name") == "web_search"
            ):
                claude_search_found = True
                assert "executor" in tool
                break

        assert (
            claude_search_found
        ), "Claude search tool should be present for Claude models"

    def test_setup_tools_with_non_claude_model(self):
        """Test setup_tools with non-Claude model does not include Claude web search tool"""
        tools = setup_tools(model="gpt-4o")

        # Ensure Claude search tool is not present
        claude_search_found = False
        for tool in tools:
            schema = tool.get("schema", {})
            if schema.get("type") == "web_search_20250305":
                claude_search_found = True
                break

        assert (
            not claude_search_found
        ), "Claude search tool should NOT be present for non-Claude models"

    def test_setup_tools_claude_search_executor(self):
        """Test Claude search tool executor"""
        from vmpilot.tools.setup_tools import claude_web_search_executor

        # Test the executor function
        result = claude_web_search_executor({"query": "test query"})
        assert isinstance(result, str)
        assert "test query" in result

    def test_is_gemini_model(self):
        """Test Gemini model detection"""
        # Test Gemini models
        assert is_gemini_model("gemini-1.5-pro") is True
        assert is_gemini_model("gemini-2.5-pro-preview-05-06") is True
        assert is_gemini_model("gemini/gemini-1.5-pro") is True
        assert is_gemini_model("Gemini-Pro") is True
        assert is_gemini_model("GEMINI-1.5-flash") is True

        # Test non-Gemini models
        assert is_gemini_model("gpt-4o") is False
        assert is_gemini_model("claude-3-sonnet") is False
        assert is_gemini_model("anthropic/claude-3-5-sonnet") is False

        # Test edge cases
        assert is_gemini_model("") is False
        assert is_gemini_model(None) is False

    def test_setup_tools_gemini_search_executor(self):
        """Test Gemini search tool executor"""
        from vmpilot.tools.setup_tools import gemini_search_executor

        # Test the executor function
        result = gemini_search_executor({"query": "test query"})
        assert isinstance(result, str)
        assert "test query" in result

        # Test without query
        result = gemini_search_executor({})
        assert isinstance(result, str)
