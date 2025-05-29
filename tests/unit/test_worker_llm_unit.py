"""
Unit tests for worker_llm.py module.

This test suite verifies the functionality of the Worker LLM implementation,
including both synchronous and asynchronous operations, edge cases, and error handling.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch  # Added AsyncMock here

import pytest
from pydantic import (  # Keep if config.get_api_key still uses it, otherwise can be removed if api_key is str
    SecretStr,
)

from vmpilot.config import Provider as APIProvider

# get_worker_llm is removed, so only import run_worker and run_worker_async
from vmpilot.worker_llm import run_worker, run_worker_async


# Mocking litellm.completion and litellm.acompletion response structure
class MockLiteLLMResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]


class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)


class MockMessage:
    def __init__(self, content):
        self.content = content


# Removed TestGetWorkerLLM class as get_worker_llm function is removed.


class TestRunWorker:
    """Tests for the run_worker function using LiteLLM."""

    @patch("litellm.completion")
    @patch("vmpilot.worker_llm.config")  # To mock config.get_api_key
    def test_run_worker_with_system_prompt(self, mock_config, mock_litellm_completion):
        """Test run_worker with both system and user prompts."""
        # Setup
        mock_config.get_api_key.return_value = "fake_api_key_for_test"
        mock_litellm_completion.return_value = MockLiteLLMResponse(
            "  LiteLLM response  "
        )

        # Execute
        result = run_worker(
            prompt="Test prompt",
            system_prompt="System instructions",
            model="test-model",  # LiteLLM model string
            provider=APIProvider.OPENAI,  # Used for API key lookup
            temperature=0.8,
            max_tokens=500,
        )

        # Verify
        mock_config.get_api_key.assert_called_once_with(APIProvider.OPENAI)
        mock_litellm_completion.assert_called_once_with(
            model="test-model",
            messages=[
                {"role": "system", "content": "System instructions"},
                {"role": "user", "content": "Test prompt"},
            ],
            temperature=0.8,
            max_tokens=500,
            api_key="fake_api_key_for_test",
        )
        assert result == "LiteLLM response"

    @patch("litellm.completion")
    @patch("vmpilot.worker_llm.config")
    def test_run_worker_without_system_prompt(
        self, mock_config, mock_litellm_completion
    ):
        """Test run_worker with only user prompt."""
        # Setup
        mock_config.get_api_key.return_value = "fake_api_key_for_test"
        mock_litellm_completion.return_value = MockLiteLLMResponse("LiteLLM response")
        # Default provider is ANTHROPIC if not specified, let's test that path for get_api_key

        # Execute
        result = run_worker(
            prompt="Test prompt",
            system_prompt="",  # Empty system prompt
            model="test-model",
            temperature=0.0,  # Explicitly set to match assertion
            max_tokens=4000,  # Explicitly set to match assertion
            # provider=APIProvider.ANTHROPIC, # Implicitly ANTHROPIC by default in run_worker
        )

        # Verify
        mock_config.get_api_key.assert_called_once_with(APIProvider.ANTHROPIC)
        mock_litellm_completion.assert_called_once_with(
            model="test-model",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.0,  # Default temperature in run_worker
            max_tokens=4000,  # Default max_tokens in run_worker
            api_key="fake_api_key_for_test",
        )
        assert result == "LiteLLM response"


class TestRunWorkerAsync:
    """Tests for the run_worker_async function using LiteLLM."""

    @pytest.mark.asyncio
    @patch(
        "litellm.acompletion", new_callable=AsyncMock
    )  # Use new_callable for async patches
    @patch("vmpilot.worker_llm.config")
    async def test_run_worker_async_with_system_prompt(
        self, mock_config, mock_litellm_acompletion
    ):
        """Test run_worker_async with both system and user prompts."""
        # Setup
        mock_config.get_api_key.return_value = "fake_async_api_key"
        mock_litellm_acompletion.return_value = MockLiteLLMResponse(
            "  Async LiteLLM response  "
        )

        # Execute
        result = await run_worker_async(
            prompt="Test async prompt",
            system_prompt="Async system instructions",
            model="test-async-model",  # LiteLLM model string
            provider=APIProvider.ANTHROPIC,  # Used for API key lookup
            temperature=0.3,
            max_tokens=800,
        )

        # Verify
        mock_config.get_api_key.assert_called_once_with(APIProvider.ANTHROPIC)
        mock_litellm_acompletion.assert_called_once_with(
            model="test-async-model",
            messages=[
                {"role": "system", "content": "Async system instructions"},
                {"role": "user", "content": "Test async prompt"},
            ],
            temperature=0.3,
            max_tokens=800,
            api_key="fake_async_api_key",
        )
        assert result == "Async LiteLLM response"

    @pytest.mark.asyncio
    @patch("litellm.acompletion", new_callable=AsyncMock)
    @patch("vmpilot.worker_llm.config")
    async def test_run_worker_async_without_system_prompt(
        self, mock_config, mock_litellm_acompletion
    ):
        """Test run_worker_async with only user prompt."""
        # Setup
        mock_config.get_api_key.return_value = "fake_async_api_key"
        mock_litellm_acompletion.return_value = MockLiteLLMResponse(
            "Async LiteLLM response"
        )

        # Execute
        result = await run_worker_async(
            prompt="Test async prompt",
            system_prompt="",  # Empty system prompt
            model="test-async-model",
            temperature=0.0,  # Explicitly set to match assertion
            max_tokens=4000,  # Explicitly set to match assertion
            # provider=APIProvider.OPENAI, # Test with a different provider for key lookup
        )

        # Verify
        mock_config.get_api_key.assert_called_once_with(
            APIProvider.ANTHROPIC
        )  # Default provider
        mock_litellm_acompletion.assert_called_once_with(
            model="test-async-model",
            messages=[{"role": "user", "content": "Test async prompt"}],
            temperature=0.0,  # Default temperature
            max_tokens=4000,  # Default max_tokens
            api_key="fake_async_api_key",
        )
        assert result == "Async LiteLLM response"


class TestErrorHandling:
    """Tests for error handling in worker_llm functions with LiteLLM."""

    @patch("litellm.completion")
    @patch("vmpilot.worker_llm.config")
    def test_run_worker_handles_litellm_error(
        self, mock_config, mock_litellm_completion
    ):
        """Test that run_worker properly handles LiteLLM errors."""
        # Setup
        mock_config.get_api_key.return_value = "key"
        # Correctly instantiate APIError for side_effect
        mock_litellm_completion.side_effect = litellm.exceptions.APIError(
            message="LiteLLM API error",
            status_code=500,
            llm_provider="test_provider",
            model="test_model",
        )

        # Execute and verify
        with pytest.raises(litellm.exceptions.APIError, match="LiteLLM API error"):
            run_worker(prompt="Test prompt")

        mock_litellm_completion.assert_called_once()

    @pytest.mark.asyncio
    @patch("litellm.acompletion", new_callable=AsyncMock)
    @patch("vmpilot.worker_llm.config")
    async def test_run_worker_async_handles_litellm_error(
        self, mock_config, mock_litellm_acompletion
    ):
        """Test that run_worker_async properly handles LiteLLM errors."""
        # Setup
        mock_config.get_api_key.return_value = "key"
        # Correctly instantiate APIError for side_effect
        mock_litellm_acompletion.side_effect = litellm.exceptions.APIError(
            message="Async LiteLLM API error",
            status_code=500,
            llm_provider="test_provider",
            model="test_model",
        )

        # Execute and verify
        with pytest.raises(
            litellm.exceptions.APIError, match="Async LiteLLM API error"
        ):
            await run_worker_async(prompt="Test async prompt")

        mock_litellm_acompletion.assert_called_once()


# Need to import litellm for the exception type
import litellm.exceptions


class TestEdgeCases:
    """Tests for edge cases in worker_llm functions with LiteLLM."""

    @patch("litellm.completion")
    @patch("vmpilot.worker_llm.config")
    def test_run_worker_with_empty_prompt(self, mock_config, mock_litellm_completion):
        """Test run_worker with an empty prompt."""
        # Setup
        mock_config.get_api_key.return_value = "key"
        mock_litellm_completion.return_value = MockLiteLLMResponse(
            "Response to empty prompt"
        )

        # Execute
        result = run_worker(prompt="")

        # Verify
        call_args = mock_litellm_completion.call_args[1]  # kwargs
        assert call_args["messages"] == [{"role": "user", "content": ""}]
        assert result == "Response to empty prompt"

    @pytest.mark.asyncio
    @patch("litellm.acompletion", new_callable=AsyncMock)
    @patch("vmpilot.worker_llm.config")
    async def test_run_worker_async_with_empty_prompt(
        self, mock_config, mock_litellm_acompletion
    ):
        """Test run_worker_async with an empty prompt."""
        # Setup
        mock_config.get_api_key.return_value = "key"
        mock_litellm_acompletion.return_value = MockLiteLLMResponse(
            "Async response to empty prompt"
        )

        # Execute
        result = await run_worker_async(prompt="")

        # Verify
        call_args = mock_litellm_acompletion.call_args[1]  # kwargs
        assert call_args["messages"] == [{"role": "user", "content": ""}]
        assert result == "Async response to empty prompt"

    @patch("litellm.completion")
    @patch("vmpilot.worker_llm.config")
    def test_run_worker_with_very_long_prompt(
        self, mock_config, mock_litellm_completion
    ):
        """Test run_worker with a very long prompt."""
        # Setup
        mock_config.get_api_key.return_value = "key"
        mock_litellm_completion.return_value = MockLiteLLMResponse(
            "Response to long prompt"
        )
        long_prompt = "x" * 10240

        # Execute
        result = run_worker(prompt=long_prompt)

        # Verify
        call_args = mock_litellm_completion.call_args[1]  # kwargs
        assert call_args["messages"] == [{"role": "user", "content": long_prompt}]
        assert result == "Response to long prompt"


# AsyncMock helper class might not be needed if unittest.mock.AsyncMock is used directly and correctly.
# If it was defined locally for a specific reason, ensure it's still needed or remove.
# For now, assuming unittest.mock.AsyncMock is sufficient when used with new_callable=AsyncMock in @patch.
# class AsyncMock(MagicMock):
#     async def __call__(self, *args, **kwargs):
#         return super(AsyncMock, self).__call__(*args, **kwargs)
