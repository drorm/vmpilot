#!/usr/bin/env python3
"""
CLI interface for interacting with vmpilot from the cli using LangChain
Usage: ./cli.py "your command here"
       ./cli.py -f input_file.txt (processes commands from a file)
       ./cli.py --coverage "your command here" (run with code coverage)
"""

# Standard library imports
import argparse
import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports (conditionally loaded)
try:
    import coverage

    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False

# Configure basic logging as early as possible
log_level = os.environ.get("PYTHONLOGLEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logging.getLogger("vmpilot").setLevel(getattr(logging, log_level))

# Explicitly silence specific loggers that might be noisy in CLI mode
for logger_name in ["vmpilot.exchange", "vmpilot.agent", "vmpilot.agent_logging"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)


# Add parent directory to Python path when running as script
def setup_path() -> None:
    """
    Add parent directory to Python path for script execution.

    This allows the script to be run directly from the command line
    without requiring the package to be installed, by adding the parent
    directory to the Python module search path.
    """
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_mock_body(temperature: float = 0.7, debug: bool = False) -> Dict:
    """
    Create a mock request body for pipeline calls.

    Args:
        temperature: The temperature setting for the LLM (controls randomness)
        debug: Whether to enable debug mode

    Returns:
        A dictionary containing the configuration for the pipeline request
    """
    from vmpilot.config import MAX_TOKENS, TOOL_OUTPUT_LINES, config

    return {
        "temperature": temperature,
        "stream": True,
        "debug": False,  # Can be enabled via -d flag
        "max_tokens": MAX_TOKENS,  # Use from config
        "tool_output_lines": TOOL_OUTPUT_LINES,  # Use from config
    }


def create_mock_messages(command: str) -> List[Dict]:
    """
    Create initial message history with the user command.

    Args:
        command: The command string provided by the user

    Returns:
        A list of message dictionaries formatted for LangChain compatibility
    """
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


async def process_command(
    command: str,
    temperature: float,
    provider: str,
    debug: bool,
) -> None:
    """Main CLI execution flow"""
    try:
        from vmpilot.chat import Chat
        from vmpilot.vmpilot import Pipeline
    except ImportError:
        # Fallback to relative imports if the module is part of a package
        from .chat import Chat
        from .vmpilot import Pipeline
    # Create pipeline with configuration
    pipeline = Pipeline()

    # Create a Chat object for this session - chat_id is determined internally
    chat = Chat()

    # Change to the project directory
    chat.change_to_project_dir()

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

                    # Print output if present
                    if output:
                        print(output, end="\n", flush=True)

                    # Print error if present
                    if error:
                        print(f"Error: {error}", end="\n", flush=True)
            else:
                # Handle error messages and other string outputs
                msg_str = str(msg).strip()
                # Skip empty messages, command echoes, and certain system messages
                skip_patterns = [command, "Executing command", "['ls"]

                if msg_str and not any(pattern in msg_str for pattern in skip_patterns):
                    # Handle error messages differently (no newline at end)
                    if msg_str.startswith("Error:"):
                        print(msg_str, flush=True)
                    else:
                        print(msg_str, end="\n", flush=True)
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI application."""
    from vmpilot.config import TEMPERATURE, CommitMessageStyle, Provider, config

    parser = argparse.ArgumentParser(
        description="VMPilot CLI",
        epilog="Examples:\n"
        "  cli.sh 'list all python files'              # Execute a single command\n"
        "  cli.sh -c 'list python files'               # Start a chat session\n"
        "  cli.sh -c 'tell me about those files'       # Continue the chat session\n"
        "  cli.sh -f commands.txt                      # Execute commands from a file one line at a time\n"
        "  cli.sh -p openai 'list all python files'    # Use a specific provider (openai, anthropic, etc.)\n"
        "  cli.sh -t 0.5 'list all python files'       # Set a specific temperature value (0.0-1.0)\n"
        "  cli.sh -v 'list all python files'           # Execute with verbose logging\n"
        "  cli.sh -d 'list all python files'           # Execute with debug logging\n"
        "  cli.sh --git 'update this file'             # Enable Git tracking for this command\n"
        "  cli.sh --no-git 'update this file'          # Disable Git tracking for this command\n"
        "  cli.sh --coverage 'list all python files'   # Execute with code coverage analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="Command to execute (not required if using -f/--file)",
    )
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
        "--coverage",
        action="store_true",
        help="Enable code coverage analysis",
    )
    parser.add_argument(
        "-c",
        "--chat",
        action="store_true",
        help="Enable chat mode to maintain conversation context between commands.",
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

    # Check for coverage flag and initialize if available
    cov = None
    if args.coverage:
        if COVERAGE_AVAILABLE:
            # generate a short unique suffix without using uuid
            suffix = str(hash(os.times()))
            cov = coverage.Coverage(data_suffix=suffix)
            cov.start()
        else:
            print(
                "Warning: Coverage module not available. Install with 'pip install coverage'"
            )

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
        try:
            print(f"Processing commands from file: {args.file}")
            if args.chat:
                print(
                    "Chat mode is not currently supported for file input. Feature planned for future release."
                )

            # Use the file path as provided (for testing compatibility)
            try:
                with open(args.file, "r") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        # Skip empty lines and comments
                        if not line or line.startswith("#"):
                            continue

                        print(f"\n--- Executing command (line {line_num}): {line} ---")
                        asyncio.run(
                            process_command(
                                line, args.temperature, args.provider, args.debug
                            )
                        )
            except FileNotFoundError:
                print(f"Error: File not found: {args.file}", file=sys.stderr)
                sys.exit(1)
            except PermissionError:
                print(
                    f"Error: Permission denied when accessing file: {args.file}",
                    file=sys.stderr,
                )
                sys.exit(1)
            except UnicodeDecodeError:
                print(
                    f"Error: Unable to decode file: {args.file}. Please ensure it is a text file.",
                    file=sys.stderr,
                )
                sys.exit(1)

            # Stop coverage and save data if enabled
            # Always append the coverage data
            if args.coverage and cov:
                cov.stop()
                cov.save()
        except KeyboardInterrupt:
            print("\nOperation canceled by user.")
            sys.exit(130)  # Standard exit code for SIGINT
        except Exception as e:
            print(f"Error processing file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    elif args.command:
        # Regular command execution
        try:
            asyncio.run(
                process_command(
                    args.command, args.temperature, args.provider, args.debug
                )
            )
        except KeyboardInterrupt:
            print("\nOperation canceled by user.")
            sys.exit(130)  # Standard exit code for SIGINT
        except Exception as e:
            print(f"Error executing command: {str(e)}", file=sys.stderr)
            sys.exit(1)
        finally:
            # Stop coverage and save data if enabled
            # Always append the coverage data
            if args.coverage and cov:
                cov.stop()
                cov.save()
    else:
        parser.error("Either a command or an input file (-f/--file) must be specified")


if __name__ == "__main__":
    setup_path()
    main()
