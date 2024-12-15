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
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": command,
                    "cache_control": {"type": "persistent"},
                }
            ],
        }
    ]


async def main(command: str, temperature: float, provider: str, model: str):
    """Main CLI execution flow"""
    pipeline = Pipeline()
    # Convert provider string to enum
    provider_enum = next(p for p in Provider if p.value == provider)
    pipeline.valves.provider = provider_enum
    pipeline.valves.model = model

    # Validate model for the specified provider
    if not config.validate_model(args.model, provider_enum):
        print(
            f"Error: '{args.model}' is not a valid model for provider '{args.provider}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Create mock pipeline call parameters
    body = create_mock_body(temperature)
    messages = create_mock_messages(command)

    # Execute pipeline
    result = pipeline.pipe(
        user_message=command, model_id=args.provider, messages=messages, body=body
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
    from vmpilot.config import Provider, config

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
        default=config.default_provider,
        choices=[p.value for p in Provider],
        help=f"API provider to use (default: {config.default_provider})",
    )

    # Add model argument with dynamic help text
    default_model = config.get_default_model()
    model_help = "Available models:\n"
    for provider in Provider:
        prov_config = config.get_provider_config(provider)
        model_help += f"\n{provider.value}: {', '.join(prov_config.available_models)}"

    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=default_model,
        help=f"Model to use (default: {default_model})\n{model_help}",
    )
    args = parser.parse_args()

    asyncio.run(main(args.command, args.temperature, args.provider, args.model))
