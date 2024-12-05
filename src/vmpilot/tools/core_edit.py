from pathlib import Path
from typing import List, Optional, Union

from .base_edit import BaseEditTool, Command, EditResult, ToolError


class CoreEditTool(BaseEditTool):
    """Core implementation of file editing operations"""

    async def execute(
        self,
        command: Command,
        path: str,
        file_text: Optional[str] = None,
        view_range: Optional[List[int]] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        insert_line: Optional[int] = None,
    ) -> EditResult:
        """Execute an edit command"""
        try:
            _path = Path(path)
            self.validate_path(command, _path)

            if command == "view":
                return await self.view(_path, view_range)
            elif command == "create":
                if file_text is None:
                    raise ToolError(
                        "Parameter `file_text` is required for command: create"
                    )
                return self.create(_path, file_text)
            elif command == "str_replace":
                if old_str is None:
                    raise ToolError(
                        "Parameter `old_str` is required for command: str_replace"
                    )
                return self.str_replace(_path, old_str, new_str)
            elif command == "insert":
                if insert_line is None:
                    raise ToolError(
                        "Parameter `insert_line` is required for command: insert"
                    )
                if new_str is None:
                    raise ToolError(
                        "Parameter `new_str` is required for command: insert"
                    )
                return self.insert(_path, insert_line, new_str)
            elif command == "undo_edit":
                return self.undo_edit(_path)

            raise ToolError(f"Unknown command: {command}")

        except ToolError as e:
            return EditResult(success=False, message=str(e), error=str(e))
        except Exception as e:
            return EditResult(
                success=False, message=f"Unexpected error: {e}", error=str(e)
            )

    async def view(
        self, path: Path, view_range: Optional[List[int]] = None
    ) -> EditResult:
        """View file or directory contents"""
        if path.is_dir():
            if view_range:
                return EditResult(
                    success=False,
                    message="view_range not allowed for directories",
                    error="The `view_range` parameter is not allowed when `path` points to a directory.",
                )

            # List non-hidden files up to 2 levels deep
            try:
                files = list(path.glob("**/[!.]*"))
                files = [f for f in files if len(f.relative_to(path).parts) <= 2]
                content = "\n".join(str(f) for f in sorted(files))
                return EditResult(
                    success=True, message=self._make_output(content, str(path))
                )
            except Exception as e:
                return EditResult(
                    success=False, message=f"Error listing directory: {e}", error=str(e)
                )

        content = self.read_file(path)
        if view_range:
            lines = content.split("\n")
            start, end = view_range
            if start < 1 or start > len(lines):
                return EditResult(
                    success=False,
                    message=f"Invalid start line: {start}",
                    error=f"Start line must be between 1 and {len(lines)}",
                )
            if end != -1:
                if end < start or end > len(lines):
                    return EditResult(
                        success=False,
                        message=f"Invalid end line: {end}",
                        error=f"End line must be between {start} and {len(lines)}",
                    )
                content = "\n".join(lines[start - 1 : end])
            else:
                content = "\n".join(lines[start - 1 :])

        return EditResult(
            success=True,
            message=self._make_output(
                content, str(path), init_line=view_range[0] if view_range else 1
            ),
        )

    def create(self, path: Path, content: str) -> EditResult:
        """Create a new file with given content"""
        try:
            self.write_file(path, content)
            self._file_history[path].append(content)
            return EditResult(
                success=True, message=f"File created successfully at: {path}"
            )
        except Exception as e:
            return EditResult(
                success=False, message=f"Failed to create file: {e}", error=str(e)
            )

    def str_replace(
        self, path: Path, old_str: str, new_str: Optional[str] = None
    ) -> EditResult:
        """Replace text in file"""
        try:
            content = self.read_file(path).expandtabs()
            old_str = old_str.expandtabs()
            new_str = new_str.expandtabs() if new_str is not None else ""

            occurrences = content.count(old_str)
            if occurrences == 0:
                return EditResult(
                    success=False,
                    message=f"Text not found in {path}",
                    error=f"No occurrences of text to replace",
                )
            elif occurrences > 1:
                lines = [
                    i + 1
                    for i, line in enumerate(content.split("\n"))
                    if old_str in line
                ]
                return EditResult(
                    success=False,
                    message=f"Multiple occurrences found in lines {lines}",
                    error="Multiple occurrences found",
                )

            new_content = content.replace(old_str, new_str)
            self._file_history[path].append(content)
            self.write_file(path, new_content)

            # Show snippet of changes
            replacement_line = content.split(old_str)[0].count("\n")
            start_line = max(0, replacement_line - self.SNIPPET_LINES)
            end_line = replacement_line + self.SNIPPET_LINES + new_str.count("\n")
            snippet = "\n".join(new_content.split("\n")[start_line : end_line + 1])

            return EditResult(
                success=True,
                message=self._make_output(
                    snippet, f"snippet of {path}", start_line + 1
                ),
            )
        except Exception as e:
            return EditResult(
                success=False, message=f"Failed to replace text: {e}", error=str(e)
            )

    def insert(self, path: Path, insert_line: int, new_str: str) -> EditResult:
        """Insert text at specified line"""
        try:
            content = self.read_file(path).expandtabs()
            new_str = new_str.expandtabs()
            lines = content.split("\n")

            if insert_line < 0 or insert_line > len(lines):
                return EditResult(
                    success=False,
                    message=f"Invalid line number: {insert_line}",
                    error=f"Line number must be between 0 and {len(lines)}",
                )

            new_lines = lines[:insert_line] + new_str.split("\n") + lines[insert_line:]
            new_content = "\n".join(new_lines)

            self._file_history[path].append(content)
            self.write_file(path, new_content)

            # Show snippet around insertion
            start_line = max(0, insert_line - self.SNIPPET_LINES)
            end_line = min(len(new_lines), insert_line + self.SNIPPET_LINES)
            snippet = "\n".join(new_lines[start_line:end_line])

            return EditResult(
                success=True,
                message=self._make_output(
                    snippet, f"snippet of {path}", start_line + 1
                ),
            )
        except Exception as e:
            return EditResult(
                success=False, message=f"Failed to insert text: {e}", error=str(e)
            )

    def undo_edit(self, path: Path) -> EditResult:
        """Undo last edit operation"""
        if not self._file_history[path]:
            return EditResult(
                success=False,
                message=f"No edit history for {path}",
                error="No history available",
            )

        try:
            previous_content = self._file_history[path].pop()
            self.write_file(path, previous_content)
            return EditResult(
                success=True, message=self._make_output(previous_content, str(path))
            )
        except Exception as e:
            return EditResult(
                success=False, message=f"Failed to undo: {e}", error=str(e)
            )
