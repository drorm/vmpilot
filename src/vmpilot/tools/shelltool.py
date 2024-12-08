import json
import logging
import platform
import subprocess
import warnings
from typing import Any, Dict, List, Optional, Type, Union

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class ShellTool(BaseTool):
    """Tool for executing shell commands."""

    name: str = "shell"
    description: str = (
        "Execute bash commands in the system. Input should be a single command string."
    )

    def _run(
        self,
        commands: Union[str, List[str]],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Run the shell command."""
        if isinstance(commands, list):
            commands = " && ".join(commands)

        try:
            output = subprocess.run(
                commands, shell=True, capture_output=True, text=True
            )
            if output.returncode != 0 and output.stderr:
                return f"Error: {output.stderr}"
            return output.stdout if output.stdout else output.stderr
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(
        self,
        commands: Union[str, List[str]],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Run the shell command asynchronously."""
        return self._run(commands, run_manager)
