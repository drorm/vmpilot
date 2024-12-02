#!/usr/bin/env python3
"""
CLI interface for interacting with vmpilot from the cli
Usage: ./cli.py "your command here"
"""

import sys
import asyncio
import argparse
import os
from typing import List, Dict
from pathlib import Path

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
    }


def create_mock_messages(command: str) -> List[Dict]:
    """Create initial message history with user command"""
    return [{"role": "user", "content": command}]


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
    for msg in result:
        print(msg, end="", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test compute.py via CLI")
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
