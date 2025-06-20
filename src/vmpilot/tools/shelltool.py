"""Tool for executing shell commands with proper output formatting."""

import logging
import subprocess
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ShellTool:
    """Wrapper to provide class interface for test compatibility"""

    def run(self, args: dict) -> str:
        # Extract command and language, pass through the shell logic
        command = args.get("command")
        language = args.get("language", "bash")
        if not command or command.strip() == "":
            return "*Command executed with no output*"
        return run_shell_command(command, language)


def run_shell_command(command, language):
    """Executes the command and returns output as string (markdown-formatted)."""
    # The below mimics the function of shell_tool executor
    import subprocess

    out = None
    try:
        out = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        if out.returncode == 0:
            return f"```{language}\n{out.stdout}```"
        else:
            return f"```{language}\n{out.stderr}```"
    except Exception as e:
        return f"```{language}\nError: {e}```"


# Tool definition for LiteLLM
shell_tool = {
    "type": "function",
    "function": {
        "name": "shell",  # Changed from shell_tool to shell to match the example
        "description": "Execute bash commands in the system. Input should be a single command string. Examples:\n"
        "            - ls /path\n"
        "            - cat file.txt\n"
        "            - head -n 10 file.md\n"
        "            - grep pattern file\n"
        "            The output will be automatically formatted with appropriate markdown syntax.",
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


def execute_shell_command(args: Dict[str, Any]) -> str:
    """Execute shell command and return formatted output."""
    command = args.get("command")
    language = args.get("language", "bash")

    if not command:
        return "Error: No command provided"

    logger.debug(f"Executing command: {command}")
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
        formatted_result = ""

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
        logger.error(f"Command timed out after 60 seconds: {command}")
        return f"Error: Command timed out after 60 seconds: {command}"
    except Exception as e:
        logger.error(f"Error executing command '{command}': {str(e)}")
        return f"Error: {str(e)}"
