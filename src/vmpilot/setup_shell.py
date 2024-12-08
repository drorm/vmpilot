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

    def _get_command_and_language(self, query: str) -> Dict[str, str]:
        # Prompt to generate the shell command and expected language
        prompt = (
            "You will help generate shell commands and predict the language for syntax highlighting.\n"
            "Based on the following input, provide the shell command to run "
            "and the expected language for the output in Markdown.\n\n"
            "Input: {query}\n"
        )

        response = self.llm.invoke(prompt)
        if hasattr(response, "content"):
            response = response.content

        try:
            result = ShellCommandResponse.parse_raw(response)
            return result.dict()
        except Exception as e:
            raise RuntimeError(f"Error parsing command response: {e}")

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

        # Determine language based on file extension
        language = "plaintext"
        if commands.endswith(".md"):
            language = "markdown"

        # Return with command as bold text before the fenced output
        return f"\n**$ {commands}**\n{self._wrap_output(language, raw_output)}"
