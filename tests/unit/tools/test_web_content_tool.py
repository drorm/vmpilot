"""Tests for the WebContentTool class."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun

from vmpilot.tools.web_content_tool import WebContentTool


class TestWebContentTool:
    """Tests for the WebContentTool class."""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        """Mock web_fetch_config for testing."""
        with patch("vmpilot.tools.web_content_tool.web_fetch_config") as mock_config:
            mock_config.enabled = True
            mock_config.max_lines = 100
            yield mock_config

    @pytest.fixture
    def mock_get_page_content(self):
        """Mock the get_page_content function."""
        with patch("vmpilot.tools.web_content_tool.get_page_content") as mock:
            mock.return_value = "Sample web content\nLine 2\nLine 3"
            yield mock

    @pytest.fixture
    def mock_run_manager(self):
        """Create a mock for the run manager."""
        manager = AsyncMock(spec=AsyncCallbackManagerForToolRun)
        manager.on_text = AsyncMock()
        return manager

    def test_init(self, mock_config):
        """Test initialization of WebContentTool."""
        tool = WebContentTool()
        assert tool.name == "web_content_fetch"
        assert "Fetch the full readable content of a web page" in tool.description

    def test_schema(self, mock_config):
        """Test schema generation."""
        tool = WebContentTool()
        schema = tool.get_schema()

        assert schema["name"] == "web_content_fetch"
        assert "description" in schema
        assert "parameters" in schema
        assert "url" in schema["parameters"]["properties"]
        assert "max_lines" in schema["parameters"]["properties"]
        assert schema["parameters"]["required"] == ["url"]

    @pytest.mark.asyncio
    async def test_arun_success(
        self, mock_config, mock_get_page_content, mock_run_manager
    ):
        """Test successful web content fetching."""
        tool = WebContentTool()
        result = await tool._arun("https://example.com", run_manager=mock_run_manager)

        # Verify the content fetcher was called correctly
        mock_get_page_content.assert_awaited_once_with(
            "https://example.com", run_manager=mock_run_manager
        )

        # Verify progress updates were sent
        assert mock_run_manager.on_text.await_count >= 2

        # Check result formatting
        assert "Sample web content" in result
        assert "Line 2" in result
        assert "Line 3" in result
        assert "````" in result  # Check for code block formatting

    @pytest.mark.asyncio
    async def test_arun_disabled(
        self, mock_config, mock_get_page_content, mock_run_manager
    ):
        """Test when web content fetching is disabled."""
        mock_config.enabled = False
        tool = WebContentTool()
        result = await tool._arun("https://example.com", run_manager=mock_run_manager)

        assert "disabled" in result
        # Verify the content fetcher was not called
        mock_get_page_content.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_arun_no_content(self, mock_config, mock_run_manager):
        """Test when no content is returned."""
        with patch("vmpilot.tools.web_content_tool.get_page_content") as mock:
            mock.return_value = None
            tool = WebContentTool()
            result = await tool._arun(
                "https://example.com", run_manager=mock_run_manager
            )

            assert "Unable to fetch" in result

    @pytest.mark.asyncio
    async def test_arun_max_lines(self, mock_config, mock_run_manager):
        """Test max_lines parameter."""
        with patch("vmpilot.tools.web_content_tool.get_page_content") as mock:
            # Create content with many lines
            mock.return_value = "\n".join([f"Line {i}" for i in range(1, 200)])

            tool = WebContentTool()
            result = await tool._arun(
                "https://example.com", max_lines=50, run_manager=mock_run_manager
            )

            # Should only show 50 lines
            assert "Line 50" in result
            assert "Line 51" not in result
            assert "Truncated" in result
            assert "149 more lines" in result

    @pytest.mark.asyncio
    async def test_arun_exception(self, mock_config, mock_run_manager):
        """Test exception handling."""
        with patch("vmpilot.tools.web_content_tool.get_page_content") as mock:
            mock.side_effect = Exception("Test error")

            tool = WebContentTool()
            result = await tool._arun(
                "https://example.com", run_manager=mock_run_manager
            )

            assert "Error fetching web content" in result
            assert "Test error" in result

            # Verify error was reported to run_manager
            mock_run_manager.on_text.assert_any_await(
                "Error: Error fetching web content: Test error\n"
            )

    def test_run_not_implemented(self, mock_config):
        """Test that _run raises NotImplementedError."""
        tool = WebContentTool()
        with pytest.raises(NotImplementedError):
            tool._run("https://example.com")
