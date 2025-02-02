from typing import Any, ClassVar, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from .core_edit import Command, CoreEditTool


class FileEditInput(BaseModel):
    """Schema for file edit operations"""

    command: Command = Field(
        ...,
        description="The edit command to execute. Use 'create' for creating new files, 'str_replace' to change text, 'insert' to add lines, 'undo_edit' to undo.",
    )
    path: str = Field(
        ...,
        description="Absolute path to the file or directory. Must start with '/' like '/tmp/hello.py'",
    )
    file_text: Optional[str] = Field(
        None,
        description="For 'create' command: The content to put in the new file. For a hello world example: 'print(\"Hello, World!\")'",
    )
    old_str: Optional[str] = Field(
        None,
        description="For 'str_replace' command: The exact text to find and replace in the file",
    )
    new_str: Optional[str] = Field(
        None,
        description="For 'str_replace' command: The new text to replace the old text with. For 'insert' command: The text to insert",
    )
    insert_line: Optional[int] = Field(
        None,
        description="For 'insert' command: Add the new text after this line number (starts at 1)",
    )


class FileEditTool(BaseTool):
    name: str = "edit_file"
    description: str = """Use this tool to edit files on the system. When given a natural language command like 'create a hello world example', translate it into the appropriate file operation. Available operations:
    - create: Create a new file with content (e.g. for a hello world example, create a Python file that prints "Hello, World!")
    - str_replace: Replace specific text in a file with new text
    - insert: Insert new text at a specific line number
    - undo_edit: Undo the last edit operation

    Note: this tool **cannot** be used to view files. Use the bash tool with commands like 'cat', 'head', 'tail', or 'less' for that.
    """
    args_schema: Type[BaseModel] = FileEditInput

    editor: Any = Field(default_factory=CoreEditTool)
    view_in_shell: bool = Field(
        default=False,
        description="If True, file viewing is disabled and should be done via shell tool",
    )

    async def _arun(self, command: Command, path: str, **kwargs) -> str:
        """Async execution of edit commands"""
        if command == "view" and self.view_in_shell:
            raise Exception(
                "File viewing operations should be done using the bash tool with commands like 'cat', 'head', 'tail', or 'less'"
            )

        result = await self.editor.execute(command, path, **kwargs)
        if not result.success:
            raise Exception(result.error or result.message)

        formatted_cmd = f"\n**$ {self._format_command(command, path, **kwargs)}**\n"
        return formatted_cmd + result.message

    MAX_DISPLAY_LENGTH: ClassVar[int] = 100  # Maximum length for displayed strings

    def _truncate_str(self, s: str, max_len: int = None) -> str:
        """Truncate string with ellipsis if too long"""
        if max_len is None:
            max_len = self.MAX_DISPLAY_LENGTH
        if len(s) <= max_len:
            return s
        return s[: max_len - 3] + "..."

    def _format_command(self, command: Command, path: str, **kwargs) -> str:
        """Format the edit command for display"""
        if command == "create":
            content = self._truncate_str(kwargs.get("file_text", ""))
            return f"create {path} '{content}'"
        elif command == "str_replace":
            old = self._truncate_str(kwargs.get("old_str", ""), 40)
            new = self._truncate_str(kwargs.get("new_str", ""), 40)
            return f"str_replace {path} '{old}' '{new}'"
        elif command == "insert":
            content = self._truncate_str(kwargs.get("new_str", ""))
            return f"insert {path} line:{kwargs.get('insert_line', 0)} '{content}'"
        elif command == "undo_edit":
            return f"undo_edit {path}"
        return f"{command} {path}"

    def _run(self, command: Command, path: str, **kwargs) -> str:
        """Synchronous execution of edit commands"""
        import asyncio

        if command == "view" and self.view_in_shell:
            raise Exception(
                "File viewing operations should be done using the bash tool with commands like 'cat', 'head', 'tail', or 'less'"
            )

        result = asyncio.run(self.editor.execute(command, path, **kwargs))
        if not result.success:
            raise Exception(result.error or result.message)

        formatted_cmd = f"\n**$ {self._format_command(command, path, **kwargs)}**\n"
        return formatted_cmd + result.message
