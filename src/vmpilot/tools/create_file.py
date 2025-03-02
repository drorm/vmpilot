from pathlib import Path
from typing import Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class FileError(Exception):
    """Base exception for file operations"""

    pass


class CreateFileInput(BaseModel):
    """Input for file creation"""

    path: str = Field(description="Path where the file should be created")
    content: str = Field(description="Content to write to the file")


class CreateFileTool(BaseTool):
    """Tool for creating new files with content"""

    name: str = "create_file"
    description: str = (
        "Create a new file with specified content. Takes path and content as input."
    )
    args_schema: Type[BaseModel] = CreateFileInput

    def _write_file(self, path: Path, content: str) -> None:
        """Write content to file, creating parent directories if needed"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        except Exception as e:
            raise FileError(f"Failed to write file {path}: {str(e)}")

    def _validate_path(self, path: Path) -> None:
        """Validate the file path"""
        if not isinstance(path, Path):
            raise ValueError("Path must be a Path object")

        # Check if path is absolute and within allowed directories
        if not path.is_absolute():
            raise ValueError("Path must be absolute")

    def _run(self, path: str, content: str) -> str:
        """Create a new file with given content"""
        try:
            file_path = Path(path)
            self._validate_path(file_path)

            # Check if file already exists
            if file_path.exists():
                raise FileExistsError(f"File already exists at: {path}")

            self._write_file(file_path, content)
            return f"\n\n**Created {file_path}.**\n\n"
        except (FileError, FileExistsError, ValueError) as e:
            raise
        except Exception as e:
            raise ValueError(f"Failed to create file: {str(e)}")

    async def _arun(self, path: str, content: str) -> str:
        """Async implementation of file creation"""
        return self._run(path, content)
