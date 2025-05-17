"""
Shell tool implementation for LiteLLM Migration MVP.
Provides shell command execution functionality.
"""

import json
import logging
import subprocess
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tool definitions
SHELL_TOOL = {
    "type": "function",
    "function": {
        "name": "shell",
        "description": "Execute bash commands in the system. Input should be a single command string.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "language": {
                    "type": "string",
                    "description": "Output language for syntax highlighting (e.g. 'bash', 'python', 'text')",
                    "default": "bash",
                },
            },
            "required": ["command"],
        },
    },
}


def execute_shell_tool(args: Dict[str, Any]) -> str:
    """Execute a shell command and return formatted output."""
    command = args.get("command")
    language = args.get("language", "bash")

    if not command:
        return "Error: No command provided"

    # Log the command
    logger.info(f"Executing shell command: {command}")

    try:
        # Execute the command
        output = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            executable="/bin/bash",
            timeout=60,  # 1-minute timeout
        )

        # Get stdout and stderr
        stdout = output.stdout.strip()
        stderr = output.stderr.strip()
        return_code = output.returncode

        # Format the output
        formatted_result = f"**$ {command}**\n"

        # Add stdout if available
        if stdout:
            formatted_result += f"\n````{language}\n{stdout}\n````\n\n"

        # Add stderr if available and there was an error
        if stderr and return_code != 0:
            formatted_result += (
                f"\n**Error (code {return_code}):**\n````text\n{stderr}\n````\n\n"
            )

        # Add a message for empty output
        if not stdout and not stderr:
            formatted_result += "\n*Command executed with no output*\n"

        return formatted_result

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after 300 seconds: {command}")
        return f"Error: Command timed out after 300 seconds: {command}"
    except Exception as e:
        logger.error(f"Error executing command '{command}': {str(e)}")
        return f"Error: {str(e)}"


def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Execute the specified tool with given arguments."""
    if tool_name == "shell":
        return execute_shell_tool(tool_args)
    else:
        return f"Error: Tool '{tool_name}' not implemented"
