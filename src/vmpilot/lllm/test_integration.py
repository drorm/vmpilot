"""
Test integration of the LiteLLM agent with the VMPilot pipeline.
This script simulates the pipeline calling generate_responses.
"""

import argparse
import logging
from typing import Any, Dict

from vmpilot.lllm.agent import generate_responses

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockPipeline:
    """Mock pipeline object that simulates the VMPilot pipeline."""

    class Valves:
        """Mock valves object with model and provider attributes."""

        def __init__(self, model):
            self.model = model

            class Provider:
                value = "openai"

            self.provider = Provider()

    def __init__(self, model="gpt-4o"):
        """Initialize the mock pipeline with a model."""
        self.valves = self.Valves(model)
        self._api_key = None  # Not used in our implementation


def main():
    """Main function for testing the integration."""
    parser = argparse.ArgumentParser(description="Test LiteLLM agent integration")
    parser.add_argument("input", help="User input")
    parser.add_argument("--model", "-m", help="Model to use", default="gpt-4o")
    args = parser.parse_args()

    # Create mock pipeline
    pipeline = MockPipeline(model=args.model)

    # Create mock body
    body: Dict[str, Any] = {"disable_logging": False}

    # Create mock messages
    messages = [{"role": "user", "content": args.input}]

    # Create mock formatted_messages
    formatted_messages = [{"role": "user", "content": args.input}]

    # Create mock system_prompt_suffix
    system_prompt_suffix = (
        "You are a helpful assistant that can execute shell commands."
    )

    # Call generate_responses
    for response in generate_responses(
        body, pipeline, messages, system_prompt_suffix, formatted_messages
    ):
        print(response)


if __name__ == "__main__":
    main()
