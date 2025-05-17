"""
CLI interface for LiteLLM Migration MVP.
Provides command-line access to the VMPilot LiteLLM agent.
"""

import argparse
import sys

from vmpilot.lllm.agent import agent_loop
from vmpilot.lllm.shelltool import SHELL_TOOL


def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(description="VMPilot LiteLLM MVP")
    parser.add_argument("input", help="User input", nargs="?")
    parser.add_argument("--model", "-m", help="Model to use", default="gpt-4o")
    args = parser.parse_args()

    # If no input provided, read from stdin
    if args.input:
        user_input = args.input
    else:
        user_input = sys.stdin.read().strip()

    if not user_input:
        print("Error: No input provided")
        return

    # Basic system prompt
    system_prompt = """You are VMPilot, an AI assistant that can help with system operations.
You can execute shell commands to help users with their tasks.
Always format command outputs with proper markdown formatting.
Be concise and helpful in your responses."""

    # Available tools
    tools = [SHELL_TOOL]

    # Run the agent loop
    response = agent_loop(user_input, system_prompt, tools, model=args.model)

    # Print the response
    print(response)


if __name__ == "__main__":
    main()
