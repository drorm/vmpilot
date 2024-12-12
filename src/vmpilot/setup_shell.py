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

    llm: BaseChatModel = Field(description="LLM to use for command generation")

    class Config:
        arbitrary_types_allowed = True

    def _detect_output_language(self, command: str, output: str) -> str:
        """Use LLM to detect the appropriate language for syntax highlighting"""
        prompt = (
            "Based on the input, generate shell commands to run and predict the language for syntax highlighting.\n"
            "The syntax highlighting is for markdown. Respond with a single word like 'python', "
            "'bash', 'json', etc. For regular command output use 'plaintext'.\n\n"
            f"Command: {command}\n"
            f"Output Sample: {output[:200]}...\n\n"
            "Language:"
        )

        response = self.llm.invoke(prompt)
        language = (
            response.content.strip().lower()
            if hasattr(response, "content")
            else response.strip().lower()
        )

        # Fallback to plaintext if language is empty or too long
        if not language or len(language) > 20:
            language = "plaintext"

        return language

    def _wrap_output(self, language: str, output: str) -> str:
        """Wrap the shell output in Markdown code fences"""
        return f"\n```{language}\n{output}\n```\n"

    def _run(
        self,
        commands: Union[str, List[str]],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        if isinstance(commands, list):
            commands = " && ".join(commands)

        # Run the shell command and capture output
        raw_output = super()._run(commands)
        logger.debug(f"Shell output: {raw_output}")

        # Detect appropriate language for the output
        language = self._detect_output_language(commands, raw_output)

        # Return with command as bold text before the fenced output
        return f"\n**$ {commands}**\n{self._wrap_output(language, raw_output)}"
