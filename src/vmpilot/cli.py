#!/usr/bin/env python3
"""
CLI interface for interacting with vmpilot from the cli using LangChain
Usage: ./cli.py "your command here"
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to Python path when running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .vmpilot import Pipeline  # Try relative import first
except ImportError:
    from vmpilot import Pipeline  # Fallback to direct import


def create_mock_body(temperature: float = 0.7) -> Dict:
    """Create a mock body for pipeline calls"""
    return {
        "temperature": temperature,
        "stream": True,
        "debug": False,  # Set to True to enable debug logging
        "max_tokens": 8192,  # For LangChain compatibility
    }


def create_mock_messages(command: str) -> List[Dict]:
    """Create initial message history with user command"""
    # Format messages for LangChain compatibility
    return [{"role": "user", "content": [{"type": "text", "text": command}]}]


async def main(command: str, temperature: float, provider: str, model: str):
    """Main CLI execution flow"""
    pipeline = Pipeline()
    pipeline.valves.PROVIDER = provider

    if provider == "openai":
        pipeline.valves.OPENAI_MODEL_ID = model
    else:
        pipeline.valves.MODEL_ID = model

    # Create mock pipeline call parameters
    body = create_mock_body(temperature)
    messages = create_mock_messages(command)

    # Execute pipeline
    result = pipeline.pipe(
        user_message=command, model_id=provider, messages=messages, body=body
    )

    # Print each message in the stream
    try:
        for msg in result:
            # Handle both string and dict outputs from LangChain
            if isinstance(msg, dict):
                if msg.get("type") == "text":
                    # Only print non-system messages
                    text = msg["text"].strip()
                    # Skip empty messages, system/debug messages, and command echoes
                    print(text, end="\n", flush=True)
                elif msg.get("type") == "tool_use":
                    # Show edit_file tool messages
                    if msg.get("name") == "edit_file":
                        print(
                            f"Executing: {msg.get('input', {})}", end="\n", flush=True
                        )
                elif msg.get("type") == "tool_output":
                    output = msg.get("output", "").strip()
                    error = msg.get("error")
                    if output:
                        print(output, end="\n", flush=True)
                    if error:
                        print(f"Error: {error}", end="\n", flush=True)
            else:
                # Handle error messages and other string outputs
                msg_str = str(msg).strip()
                if msg_str and not any(
                    x in msg_str for x in [command, "Executing command", "['ls"]
                ):
                    if msg_str.startswith("Error:"):
                        print(msg_str, flush=True)
                    else:
                        print(msg_str, end="\n", flush=True)
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VMPilot CLI using LangChain")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for response generation (default: 0.7)",
    )
    parser.add_argument(
        "-p",
        "--provider",
        type=str,
        default="anthropic",
        choices=["anthropic", "openai"],
        help="API provider to use (default: anthropic)",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="claude-3-5-sonnet-20241022",
        help="Model to use (default: claude-3-5-sonnet-20241022 for Anthropic, gpt-4 for OpenAI)",
    )
    args = parser.parse_args()

    asyncio.run(main(args.command, args.temperature, args.provider, args.model))
