"""
Setup shell tool for VMPilot.
Provides a wrapper around the shell command execution functionality.
"""

import logging
import os
from typing import Any, Dict, Optional

# Export the shell tool definition for use in the agent
from .tools.shelltool import SHELL_TOOL, execute_shell_command

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


# For LangChain compatibility
try:
    from langchain_core.callbacks import CallbackManagerForToolRun
    from pydantic import BaseModel

    from .tools.shelltool import ShellTool as LangchainShellTool

    class ShellCommandResponse(BaseModel):
        """Model for structured shell command response"""

        command: str
        language: str = "plaintext"

    class SetupShellTool(LangchainShellTool):
        """Tool for executing shell commands with markdown formatting"""

        def _run(
            self,
            command: str,
            language: str = "bash",
            run_manager: Optional[CallbackManagerForToolRun] = None,
        ) -> str:
            # Execute command with proper language formatting
            result = super()._run(
                command=command, language=language, run_manager=run_manager
            )

            return f"\n{result}"

except ImportError:
    # If LangChain is not available, provide a stub
    class SetupShellTool:
        """Stub for when LangChain is not available"""

        def __init__(self, *args, **kwargs):
            raise ImportError("LangChain is not available")
