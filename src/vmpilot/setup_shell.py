import logging
from typing import Dict, List, Optional, Union

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from .tools.shelltool import ShellTool

logger = logging.getLogger(__name__)


class ShellCommandResponse(BaseModel):
    """Model for structured shell command response"""

    command: str
    language: str = "plaintext"


class SetupShellTool(ShellTool):
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

        # Add the original command as a bold header before the output
        return f"\n**$ {command}**\n{result}"
