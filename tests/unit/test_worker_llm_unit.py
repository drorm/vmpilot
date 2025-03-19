"""
Unit tests for worker_llm.py module.

This test suite verifies the functionality of the Worker LLM implementation,
including both synchronous and asynchronous operations, edge cases, and error handling.
"""

import asyncio
from unittest.mock import MagicMock, Mock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from vmpilot.config import Provider as APIProvider
from vmpilot.worker_llm import get_worker_llm, run_worker, run_worker_async


class TestGetWorkerLLM:
    """Tests for the get_worker_llm function."""

    @patch("vmpilot.worker_llm.ChatOpenAI")
    @patch("vmpilot.worker_llm.config")
    def test_get_openai_worker(self, mock_config, mock_chat_openai):
        """Test that get_worker_llm returns OpenAI worker with correct parameters."""
        # Setup
        mock_config.get_api_key.return_value = "fake-api-key"
        mock_chat_openai.return_value = "openai-instance"

        # Execute
        result = get_worker_llm(
            model="gpt-4-turbo",
            provider=APIProvider.OPENAI,
            temperature=0.5,
            max_tokens=1000,
        )

        # Verify
        mock_config.get_api_key.assert_called_once_with(APIProvider.OPENAI)
        mock_chat_openai.assert_called_once_with(
            model="gpt-4-turbo",
            temperature=0.5,
            max_tokens=1000,
            api_key="fake-api-key",
        )
        assert result == "openai-instance"

    @patch("vmpilot.worker_llm.ChatAnthropic")
    @patch("vmpilot.worker_llm.config")
    def test_get_anthropic_worker(self, mock_config, mock_chat_anthropic):
        """Test that get_worker_llm returns Anthropic worker with correct parameters."""
        # Setup
        mock_config.get_api_key.return_value = "fake-api-key"
        mock_chat_anthropic.return_value = "anthropic-instance"

        # Execute
        result = get_worker_llm(
            model="claude-3-opus-20240229",
            provider=APIProvider.ANTHROPIC,
            temperature=0.7,
            max_tokens=2000,
        )

        # Verify
        mock_config.get_api_key.assert_called_once_with(APIProvider.ANTHROPIC)
        mock_chat_anthropic.assert_called_once_with(
            model="claude-3-opus-20240229",
            temperature=0.7,
            max_tokens=2000,
            api_key="fake-api-key",
        )
        assert result == "anthropic-instance"

    def test_get_unsupported_provider(self):
        """Test that get_worker_llm raises ValueError for unsupported provider."""
        # Define a mock unsupported provider
        unsupported_provider = "UNSUPPORTED"

        # Execute and verify
        with pytest.raises(
            ValueError, match=f"Unsupported provider: {unsupported_provider}"
        ):
            get_worker_llm(provider=unsupported_provider)


class TestRunWorker:
    """Tests for the run_worker function."""

    @patch("vmpilot.worker_llm.get_worker_llm")
    def test_run_worker_with_system_prompt(self, mock_get_worker_llm):
        """Test run_worker with both system and user prompts."""
        # Setup
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "  LLM response  "
        mock_llm.invoke.return_value = mock_response
        mock_get_worker_llm.return_value = mock_llm

        # Execute
        result = run_worker(
            prompt="Test prompt",
            system_prompt="System instructions",
            model="test-model",
            provider=APIProvider.OPENAI,
            temperature=0.8,
            max_tokens=500,
        )

        # Verify
        mock_get_worker_llm.assert_called_once_with(
            model="test-model",
            provider=APIProvider.OPENAI,
            temperature=0.8,
            max_tokens=500,
        )

        # Check that both system and human messages were included
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 2
        assert isinstance(call_args[0], SystemMessage)
        assert call_args[0].content == "System instructions"
        assert isinstance(call_args[1], HumanMessage)
        assert call_args[1].content == "Test prompt"

        # Check that whitespace was stripped from response
        assert result == "LLM response"

    @patch("vmpilot.worker_llm.get_worker_llm")
    def test_run_worker_without_system_prompt(self, mock_get_worker_llm):
        """Test run_worker with only user prompt."""
        # Setup
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "LLM response"
        mock_llm.invoke.return_value = mock_response
        mock_get_worker_llm.return_value = mock_llm

        # Execute
        result = run_worker(
            prompt="Test prompt",
            system_prompt="",  # Empty system prompt
            model="test-model",
        )

        # Verify
        # Check that only human message was included
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], HumanMessage)
        assert call_args[0].content == "Test prompt"

        assert result == "LLM response"


class TestRunWorkerAsync:
    """Tests for the run_worker_async function."""

    @pytest.mark.asyncio
    @patch("vmpilot.worker_llm.get_worker_llm")
    async def test_run_worker_async_with_system_prompt(self, mock_get_worker_llm):
        """Test run_worker_async with both system and user prompts."""
        # Setup
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "  Async LLM response  "

        # Setup the async mock
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_worker_llm.return_value = mock_llm

        # Execute
        result = await run_worker_async(
            prompt="Test async prompt",
            system_prompt="Async system instructions",
            model="test-async-model",
            provider=APIProvider.ANTHROPIC,
            temperature=0.3,
            max_tokens=800,
        )

        # Verify
        mock_get_worker_llm.assert_called_once_with(
            model="test-async-model",
            provider=APIProvider.ANTHROPIC,
            temperature=0.3,
            max_tokens=800,
        )

        # Check that both system and human messages were included
        call_args = mock_llm.ainvoke.call_args[0][0]
        assert len(call_args) == 2
        assert isinstance(call_args[0], SystemMessage)
        assert call_args[0].content == "Async system instructions"
        assert isinstance(call_args[1], HumanMessage)
        assert call_args[1].content == "Test async prompt"

        # Check that whitespace was stripped from response
        assert result == "Async LLM response"

    @pytest.mark.asyncio
    @patch("vmpilot.worker_llm.get_worker_llm")
    async def test_run_worker_async_without_system_prompt(self, mock_get_worker_llm):
        """Test run_worker_async with only user prompt."""
        # Setup
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Async LLM response"

        # Setup the async mock
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_worker_llm.return_value = mock_llm

        # Execute
        result = await run_worker_async(
            prompt="Test async prompt",
            system_prompt="",  # Empty system prompt
            model="test-async-model",
        )

        # Verify
        # Check that only human message was included
        call_args = mock_llm.ainvoke.call_args[0][0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], HumanMessage)
        assert call_args[0].content == "Test async prompt"

        assert result == "Async LLM response"


class TestErrorHandling:
    """Tests for error handling in worker_llm functions."""

    @patch("vmpilot.worker_llm.get_worker_llm")
    def test_run_worker_handles_llm_error(self, mock_get_worker_llm):
        """Test that run_worker properly handles LLM errors."""
        # Setup - LLM that raises an exception
        mock_llm = Mock()
        mock_llm.invoke.side_effect = ValueError("API error")
        mock_get_worker_llm.return_value = mock_llm

        # Execute and verify
        with pytest.raises(ValueError, match="API error"):
            run_worker(prompt="Test prompt")

        # Verify the LLM was called
        mock_llm.invoke.assert_called_once()

    @pytest.mark.asyncio
    @patch("vmpilot.worker_llm.get_worker_llm")
    async def test_run_worker_async_handles_llm_error(self, mock_get_worker_llm):
        """Test that run_worker_async properly handles LLM errors."""
        # Setup - LLM that raises an exception
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(side_effect=ValueError("Async API error"))
        mock_get_worker_llm.return_value = mock_llm

        # Execute and verify
        with pytest.raises(ValueError, match="Async API error"):
            await run_worker_async(prompt="Test async prompt")

        # Verify the LLM was called
        mock_llm.ainvoke.assert_called_once()


class TestEdgeCases:
    """Tests for edge cases in worker_llm functions."""

    @patch("vmpilot.worker_llm.get_worker_llm")
    def test_run_worker_with_empty_prompt(self, mock_get_worker_llm):
        """Test run_worker with an empty prompt."""
        # Setup
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Response to empty prompt"
        mock_llm.invoke.return_value = mock_response
        mock_get_worker_llm.return_value = mock_llm

        # Execute
        result = run_worker(prompt="")

        # Verify
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].content == ""  # Empty prompt
        assert result == "Response to empty prompt"

    @pytest.mark.asyncio
    @patch("vmpilot.worker_llm.get_worker_llm")
    async def test_run_worker_async_with_empty_prompt(self, mock_get_worker_llm):
        """Test run_worker_async with an empty prompt."""
        # Setup
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Async response to empty prompt"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_worker_llm.return_value = mock_llm

        # Execute
        result = await run_worker_async(prompt="")

        # Verify
        call_args = mock_llm.ainvoke.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].content == ""  # Empty prompt
        assert result == "Async response to empty prompt"

    @patch("vmpilot.worker_llm.get_worker_llm")
    def test_run_worker_with_very_long_prompt(self, mock_get_worker_llm):
        """Test run_worker with a very long prompt."""
        # Setup
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Response to long prompt"
        mock_llm.invoke.return_value = mock_response
        mock_get_worker_llm.return_value = mock_llm

        # Create a long prompt (10KB)
        long_prompt = "x" * 10240

        # Execute
        result = run_worker(prompt=long_prompt)

        # Verify
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].content == long_prompt
        assert result == "Response to long prompt"


# Helper class for async mocking
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
