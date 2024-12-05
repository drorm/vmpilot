from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, get_args

Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]


@dataclass
class EditResult:
    """Result from an edit operation"""

    success: bool
    message: str
    error: Optional[str] = None


class ToolError(Exception):
    """Base class for tool errors"""

    pass


class BaseEditTool:
    """Base class for file editing operations"""

    SNIPPET_LINES: int = 4

    def __init__(self):
        self._file_history = defaultdict(list)

    def validate_path(self, command: str, path: Path):
        """Check that the path/command combination is valid."""
        if not path.is_absolute():
            suggested_path = Path("") / path
            raise ToolError(
                f"The path {path} is not an absolute path, it should start with `/`. Maybe you meant {suggested_path}?"
            )
        if not path.exists() and command != "create":
            raise ToolError(
                f"The path {path} does not exist. Please provide a valid path."
            )
        if path.exists() and command == "create":
            raise ToolError(
                f"File already exists at: {path}. Cannot overwrite files using command `create`."
            )
        if path.is_dir() and command != "view":
            raise ToolError(
                f"The path {path} is a directory and only the `view` command can be used on directories"
            )

    def read_file(self, path: Path) -> str:
        """Read the content of a file from a given path"""
        try:
            return path.read_text()
        except Exception as e:
            raise ToolError(f"Error reading {path}: {e}") from None

    def write_file(self, path: Path, content: str):
        """Write content to a file at given path"""
        try:
            path.write_text(content)
        except Exception as e:
            raise ToolError(f"Error writing to {path}: {e}") from None

    def _make_output(
        self,
        file_content: str,
        file_descriptor: str,
        init_line: int = 1,
        expand_tabs: bool = True,
    ) -> str:
        """Format file content with line numbers"""
        if expand_tabs:
            file_content = file_content.expandtabs()

        numbered_lines = [
            f"{i + init_line:6}\t{line}"
            for i, line in enumerate(file_content.split("\n"))
        ]
        return (
            f"Here's the result of running `cat -n` on {file_descriptor}:\n```\n"
            + "\n".join(numbered_lines)
            + "\n```\n"
        )

    def maybe_truncate(self, text: str, max_length: int = 2000) -> str:
        """Truncate text if it exceeds max_length"""
        if len(text) > max_length:
            return text[:max_length] + "\n<output truncated>"
        return text
