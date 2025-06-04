"""
Unit tests for the Usage class with OpenAI token tracking.
"""

import unittest
from unittest.mock import MagicMock

from vmpilot.config import Provider
from vmpilot.usage import Usage


class TestUsageOpenAI(unittest.TestCase):
    """Test the Usage class with OpenAI token tracking."""

    def setUp(self):
        """Set up test fixtures."""
        self.usage = Usage(provider=Provider.OPENAI)

    def test_add_tokens_openai_format(self):
        """Test adding tokens from OpenAI format."""
        # Create a mock message with OpenAI token usage
        mock_message = MagicMock()

        # Set response_metadata with token_usage
        mock_message.response_metadata = {
            "model_name": "gpt-4.1-2025-04-14",
            "system_fingerprint": "fp_b38e740b47",
            "finish_reason": "stop",
            "token_usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "prompt_tokens_details": {"cached_tokens": 20},
            },
        }

        # Add tokens from the mock message
        self.usage.add_tokens(mock_message)

        # Check that the tokens were added correctly
        self.assertEqual(self.usage.input_tokens, 80)
        self.assertEqual(self.usage.output_tokens, 50)
        self.assertEqual(self.usage.cache_read_input_tokens, 20)
        self.assertEqual(self.usage.model_name, "gpt-4.1-2025-04-14")


if __name__ == "__main__":
    unittest.main()
