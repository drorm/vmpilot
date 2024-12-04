from langchain_community.tools import ShellTool
from langchain_anthropic import ChatAnthropic
from pydantic import Field
import json
from typing import Union, List


class FenceShellTool(ShellTool):
    llm: ChatAnthropic = Field(description="LLM to use for command generation")

    class Config:
        arbitrary_types_allowed = True

    def _get_command_and_language(self, query: str) -> dict:
        # Prompt to generate the shell command and expected language
        prompt = (
            "You will help generate shell commands and predict the language for syntax highlighting.\n"
            "Based on the following input, return a JSON response with the shell command to run "
            "and the expected language for the output in Markdown.\n\n"
            "Input:\n{query}\n\n"
            "JSON format:\n"
            "{\n"
            '  "command": "<shell command>",\n'
            '  "language": "<expected language>"\n'
            "}\n\n"
            "Only respond with valid JSON."
        )
        response = self.llm.invoke(f"{prompt}\nInput: {query}")
        if hasattr(response, "content"):
            response = response.content
        return json.loads(response)

    def _wrap_output(self, language: str, output: str) -> str:
        # Wrap the shell output in Markdown code fences
        return f"```{language}\n{output}\n```"

    def _run(self, commands: Union[str, List[str]]) -> str:
        if isinstance(commands, list):
            commands = " ".join(commands)

        # Get command and expected language
        result = self._get_command_and_language(commands)
        command = result["command"]
        language = result["language"]

        # Run the shell command and capture output
        raw_output = super()._run(command)

        # Return the wrapped output
        return self._wrap_output(language, raw_output)
