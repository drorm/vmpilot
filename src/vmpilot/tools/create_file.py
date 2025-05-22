from pathlib import Path
from typing import Any, Dict


class FileError(Exception):
    """Base exception for file operations"""

    pass


def _write_file(path: Path, content: str) -> None:
    """Write content to file, creating parent directories if needed"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    except Exception as e:
        raise FileError(f"Failed to write file {path}: {str(e)}")


def _validate_path(path: Path) -> None:
    """Validate the file path"""
    if not isinstance(path, Path):
        raise ValueError("Path must be a Path object")

    # Check if path is absolute and within allowed directories
    if not path.is_absolute():
        raise ValueError("Path must be absolute")


def create_file_executor(args: Dict[str, Any]) -> str:
    """
    LiteLLM-compatible executor function for creating files.

    Args:
        args: Dictionary containing 'path' and 'content' keys

    Returns:
        Success message string
    """
    path = args.get("path")
    content = args.get("content")

    if not path:
        raise ValueError("Missing required parameter: path")
    if content is None:  # Allow empty content
        content = ""

    try:
        file_path = Path(path)
        _validate_path(file_path)

        # Check if file already exists
        if file_path.exists():
            return f"Error: File already exists at: {path}. Either remove first or use the edit_file tool to modify existing files."

        _write_file(file_path, content)
        return f"\n\n**Created {file_path}**\n\n"
    except (FileError, FileExistsError, ValueError) as e:
        raise
    except Exception as e:
        raise ValueError(f"Failed to create file: {str(e)}")


def get_create_file_schema() -> Dict[str, Any]:
    """Get the LiteLLM schema for the create_file tool."""
    return {
        "name": "create_file",
        "description": "Create a new file with specified content. Takes path and content as input.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path where the file should be created",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        },
    }
