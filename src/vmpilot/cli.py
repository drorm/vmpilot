#!/usr/bin/env python3
"""
CLI interface for interacting with vmpilot from the cli using LangChain
Usage: ./cli.py "your command here"
       ./cli.py -f input_file.txt (processes commands from a file)
"""

import argparse
import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional

# Configure basic logging as early as possible
log_level = os.environ.get("PYTHONLOGLEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logging.getLogger("vmpilot").setLevel(getattr(logging, log_level))

# Explicitly silence specific loggers that might be noisy in CLI mode
for logger_name in ["vmpilot.exchange", "vmpilot.agent", "vmpilot.agent_logging"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

# Add parent directory to Python path when running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from vmpilot.chat import Chat
    from vmpilot.vmpilot import Pipeline
except ImportError:
    # Fallback to relative imports if the module is part of a package
    from .chat import Chat
    from .vmpilot import Pipeline


def create_mock_body(temperature: float = 0.7, debug: bool = False) -> Dict:
    """Create a mock body for pipeline calls"""
    from vmpilot.config import MAX_TOKENS, TOOL_OUTPUT_LINES, config

    return {
        "temperature": temperature,
        "stream": True,
        "debug": False,  # Can be enabled via -d flag
        "max_tokens": MAX_TOKENS,  # Use from config
        "tool_output_lines": TOOL_OUTPUT_LINES,  # Use from config
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
                }
            ],
        }
    ]


async def main(
    command: str,
    temperature: float,
    provider: str,
    debug: bool,
    chat_id: Optional[str] = None,
):
    """Main CLI execution flow"""
    # Create pipeline with configuration
    pipeline = Pipeline()

    # Create a Chat object for this session
    chat = Chat(chat_id=chat_id)

    # Change to the project directory when starting a new chat
    if not chat_id:
        chat.change_to_project_dir()
        if debug:
            logging.debug(f"Changed to project directory: {chat.project_dir}")

    # Set chat ID for conversation persistence if provided
    if chat_id:
        pipeline.chat_id = chat_id
        if debug:
            logging.debug(f"Using chat context with ID: {chat_id}")

    # Create pipeline call parameters
    body = create_mock_body(temperature=temperature, debug=debug)
    messages = create_mock_messages(command)

    # Set provider before executing pipeline
    pipeline.set_provider(provider)

    # Update configuration
    pipeline.valves._sync_with_config()

    # Execute pipeline with configuration
    result = pipeline.pipe(
        user_message=command,
        model_id="",  # Use default model for provider
        messages=messages,
        body=body,
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
    from vmpilot.config import CommitMessageStyle, Provider, config

    parser = argparse.ArgumentParser(
        description="VMPilot CLI",
        epilog="Examples:\n"
        "  cli.sh 'list all python files'              # Execute a single command\n"
        "  cli.sh -c 'list python files'               # Start a chat session\n"
        "  cli.sh -c 'tell me about those files'       # Continue the chat session\n"
        "  cli.sh -f commands.txt                      # Execute commands from a file one line at the time\n"
        "  cli.sh -f commands.txt -c                   # Execute commands from a file one line at the time with chat context\n"
        "  cli.sh -v 'list all python files'           # Execute with verbose logging\n"
        "  cli.sh -d 'list all python files'           # Execute with debug logging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="Command to execute (not required if using -f/--file)",
    )
    from vmpilot.config import TEMPERATURE

    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=TEMPERATURE,
        help=f"Temperature for response generation (default: {TEMPERATURE})",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Input file with commands (one per line)",
    )
    parser.add_argument(
        "-p",
        "--provider",
        type=str,
        default=config.default_provider,
        choices=[p.value for p in Provider],
        help=f"API provider to use (default: {config.default_provider})",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed logging",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output with INFO level logging",
    )
    parser.add_argument(
        "-c",
        "--chat",
        nargs="?",
        const=str(uuid.uuid4()),  # Generate a random ID if flag is used without value
        help="Enable chat mode to maintain conversation context. Optional: provide a specific chat ID.",
    )

    # Git tracking options (use defaults from config)
    parser.add_argument(
        "--git",
        action="store_true",
        dest="git_override",
        help="Override: Enable Git tracking for LLM-generated changes",
    )
    parser.add_argument(
        "--no-git",
        action="store_false",
        dest="git_override",
        help="Override: Disable Git tracking for LLM-generated changes",
    )

    args = parser.parse_args()

    # Configure logging based on debug and verbose flags
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("vmpilot").setLevel(logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("vmpilot").setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("vmpilot").setLevel(logging.WARNING)

    # Override Git configuration from command line if specified
    if hasattr(args, "git_override") and args.git_override is not None:
        config.git_config.enabled = args.git_override
        logging.info(
            f"Git tracking {'enabled' if args.git_override else 'disabled'} via command line"
        )

    # Check if file input is provided
    if args.file:
        # Generate a random chat ID if chat mode is enabled without a specific ID
        chat_id = (
            args.chat
            if args.chat
            else str(uuid.uuid4()) if args.chat is not None else None
        )

        # Convert to absolute path if it's a relative path
        file_path = os.path.abspath(args.file)

        try:
            print(f"Processing commands from file: {args.file}")
            if chat_id:
                print(f"Using chat ID: {chat_id}")

            with open(file_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    print(f"\n--- Executing command (line {line_num}): {line} ---")
                    asyncio.run(
                        main(line, args.temperature, args.provider, args.debug, chat_id)
                    )
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error processing file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    elif args.command:
        # Regular command execution
        asyncio.run(
            main(args.command, args.temperature, args.provider, args.debug, args.chat)
        )
    else:
        parser.error("Either a command or an input file (-f/--file) must be specified")
