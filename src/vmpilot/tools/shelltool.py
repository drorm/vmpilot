"""Tool for executing shell commands with proper output formatting."""

import logging
import subprocess
from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ShellInput(BaseModel):
    """Input schema for shell commands."""

    command: str = Field(description="The shell command to execute")
    language: str = Field(
        default="bash",
        description="Output language for syntax highlighting (e.g. 'bash', 'python', 'text')",
    )


class ShellTool(BaseTool):
    """Tool for executing shell commands with formatted output."""

    name: str = "shell"
    description: str = """Execute bash commands in the system. Input should be a single command string. Examples:
            - ls /path
            - cat file.txt
            - head -n 10 file.md
            - grep pattern file
            The output will be automatically formatted with appropriate markdown syntax."""
    args_schema: Type[BaseModel] = ShellInput

    def _run(
        self,
        command: str,
        language: str = "bash",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute shell command and return formatted output."""
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

    async def _arun(
        self,
        command: str,
        language: str = "bash",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Run the shell command asynchronously."""
        return self._run(command=command, language=language, run_manager=run_manager)
