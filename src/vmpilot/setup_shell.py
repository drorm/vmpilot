"""
Setup shell tool for VMPilot.
Provides a wrapper around the shell command execution functionality.
"""

import logging
from typing import Any, Dict, Optional, Type

# Export the shell tool definition for use in the agent
from .tools.shelltool import SHELL_TOOL, execute_shell_command

# Export the shell tool definition for LiteLLM compatibility
SETUP_SHELL_TOOL = SHELL_TOOL

logger = logging.getLogger(__name__)


def execute_setup_shell_command(args: Dict[str, Any]) -> str:
    """
    Execute a shell command with additional formatting.
    This is a wrapper around the base shell command execution.
    """
    # Execute command with proper language formatting
    result = execute_shell_command(args)

    # Add a newline before the result for better formatting
    return f"\n{result}"


# We need these for compatibility with the current agent architecture
from pydantic import BaseModel, Field


class ShellCommandInput(BaseModel):
    """Input schema for shell commands."""

    command: str = Field(description="The shell command to execute")
    language: str = Field(
        default="bash",
        description="Output language for syntax highlighting (e.g. 'bash', 'python', 'text')",
    )


class SetupShellTool:
    """Tool for executing shell commands with markdown formatting"""

    name: str = "shell"
    description: str = """Execute bash commands in the system. Input should be a single command string. Examples:
            - ls /path
            - cat file.txt
            - head -n 10 file.md
            - grep pattern file
            The output will be automatically formatted with appropriate markdown syntax."""
    args_schema: Type[BaseModel] = ShellCommandInput

    def _run(self, command: str, language: str = "bash", **kwargs) -> str:
        """Execute shell command and return formatted output."""
        args = {"command": command, "language": language}
        result = execute_shell_command(args)

        # Add a newline before the result for better formatting
        return f"\n{result}"

    async def _arun(self, command: str, language: str = "bash", **kwargs) -> str:
        """Run the shell command asynchronously."""
        return self._run(command=command, language=language, **kwargs)
