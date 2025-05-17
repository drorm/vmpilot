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

    try:
        # Execute the command
        output = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            executable="/bin/bash",
        )

        # Combine stdout and stderr if there's an error
        if output.returncode != 0:
            result = f"{output.stdout}\n{output.stderr}".strip()
        else:
            result = output.stdout.strip()

        # Format the output with the specified language and include the original command
        formatted_result = f"**$ {command}**\n"
        if result:
            # we use 4 backticks to escape the 3 backticks that might be in the markdown
            formatted_result += f"\n````{language}\n{result}\n````\n\n"
        return formatted_result

    except Exception as e:
        logger.error(f"Error executing command '{command}': {str(e)}")
        return f"Error: {str(e)}"


def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Execute the specified tool with given arguments."""
    if tool_name == "shell":
        return execute_shell_tool(tool_args)
    else:
        return f"Error: Tool '{tool_name}' not implemented"
