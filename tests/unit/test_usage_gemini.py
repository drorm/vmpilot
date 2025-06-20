"""
Test Gemini token usage tracking implementation.
"""

from unittest.mock import MagicMock

import pytest

from vmpilot.config import Provider
from vmpilot.usage import Usage


def test_gemini_token_tracking():
    """Test that Gemini token usage is tracked correctly."""
    # Create a usage tracker for Gemini
    usage = Usage(provider=Provider.GOOGLE)

    # Create a mock message with token usage in response_metadata
    mock_message = MagicMock()
    mock_message.response_metadata = {
        "model_name": "gemini-2.5-pro-exp-03-25",
        "prompt_feedback": {"block_reason": 0, "safety_ratings": []},
        "finish_reason": "STOP",
        "token_usage": {
            "prompt_tokens": 3328,
            "completion_tokens": 18,
            "total_tokens": 3346,
            "prompt_tokens_details": {"cached_tokens": 200},
        },
    }

    # Add the tokens from the mock message
    usage.add_tokens(mock_message)

    # Check that the tokens were tracked correctly
    totals = usage.get_totals()
    assert totals["input_tokens"] == 3128
    assert totals["output_tokens"] == 18
    assert totals["cache_read_input_tokens"] == 200
    assert totals["model"] == "gemini-2.5-pro-exp-03-25"

    # Test cost calculation
    costs = usage.calculate_cost()
    assert "input_cost" in costs
    assert "output_cost" in costs
    assert "cache_read_cost" in costs
    assert "total_cost" in costs


def test_gemini_cost_message():
    """Test that the cost message for Gemini is formatted correctly."""
    # Create a usage tracker for Gemini
    usage = Usage(provider=Provider.GOOGLE)

    # Create a mock message with token usage in response_metadata
    mock_message = MagicMock()
    mock_message.response_metadata = {
        "model_name": "gemini-2.5-pro-exp-03-25",
        "token_usage": {
            "prompt_tokens": 3328,
            "completion_tokens": 18,
            "total_tokens": 3346,
            "prompt_tokens_details": {"cached_tokens": 200},
        },
    }

    # Add the tokens from the mock message
    usage.add_tokens(mock_message)

    # Get the cost message
    cost_message = usage.get_cost_message()

    # Check that it contains the expected elements
    assert "Total" in cost_message
    assert "Input" in cost_message
    assert "Output" in cost_message
    assert "Cache Read" in cost_message
