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
        "disable_logging": True,  # Disable logging when running from CLI
        "max_tokens": 8192,  # For LangChain compatibility
    }


def create_mock_messages(command: str) -> List[Dict]:
    """Create initial message history with user command"""
    # Format messages for LangChain compatibility
    return [
        {
            "role": "user",
            "content": [{"type": "text", "text": command}]
        }
    ]


async def main(command: str, temperature: float):
    """Main CLI execution flow"""
    pipeline = Pipeline()

    # Create mock pipeline call parameters
    body = create_mock_body(temperature)
    messages = create_mock_messages(command)

    # Execute pipeline
    model_id = os.getenv("MODEL_ID", "VMPilot")
    result = pipeline.pipe(
        user_message=command, model_id=model_id, messages=messages, body=body
    )

    # Print each message in the stream
    try:
        for msg in result:
            # Handle both string and dict outputs from LangChain
            if isinstance(msg, dict):
                if msg.get("type") == "text":
                    print(msg["text"], end="", flush=True)
                elif msg.get("type") == "tool_use":
                    name = msg.get("name", "unknown")
                    input_data = msg.get("input", {})
                    if name == "terminal":
                        cmd = input_data.get("commands", "")
                        print(f"\n$ {cmd}", end="", flush=True)
                elif msg.get("type") == "tool_result":
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        print(f"\n{content}", end="", flush=True)
                    else:
                        print(f"\n{str(content)}", end="", flush=True)
            else:
                print(str(msg), end="", flush=True)
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
    args = parser.parse_args()

    asyncio.run(main(args.command, args.temperature))
