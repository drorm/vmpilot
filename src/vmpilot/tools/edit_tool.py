#!/usr/bin/env python
#
# This file uses concepts from the Aider project (https://github.com/Aider-AI/aider)
# which is licensed under the Apache License, Version 2.0

import logging
from pathlib import Path
from typing import Any, Dict

from .edit_diff import do_replace, find_original_update_blocks

logger = logging.getLogger(__name__)


def edit_file_executor(args: Dict[str, Any]) -> str:
    """
    LiteLLM-compatible executor function for editing files using aider's diff format.

    Args:
        args: Dictionary containing 'content' key with the diff content

    Returns:
        Success message string
    """
    content = args.get("content")

    if not content:
        raise ValueError("Missing required parameter: content")

    try:
        # Use aider's built-in diff block parser to validate and extract edits
        edits = list(find_original_update_blocks(content))
        if not edits:
            raise ValueError("Invalid diff format")

        # Check if all files exist before proceeding
        for edit in edits:
            file_path = Path(
                edit[0]
            ).expanduser()  # First element of edit tuple is the file path, expand ~ if present
            logger.debug(f"Checking file path: {file_path}")
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

        # Apply the edits directly to the files
        edited_files = []
        for file_path, original, replacement in edits:
            file = Path(file_path).expanduser()
            with open(file, "r") as f:
                file_content = f.read()
            new_content = do_replace(file, file_content, original, replacement)
            if new_content is not None:
                with open(file, "w") as f:
                    f.write(new_content)
                edited_files.append(str(file))
            else:
                return "No matches found"

        if len(edited_files) == 1:
            return f"\n\n**Edited {edited_files[0]}.**\n\n"
        else:
            return f"\n\n**Edited {len(edited_files)} files: {', '.join(edited_files)}.**\n\n"

    except FileNotFoundError:
        raise
    except ValueError:
        logger.info(f"Error value in edit {content}")
        raise


def get_edit_file_schema() -> Dict[str, Any]:
    """Get the LiteLLM schema for the edit_file tool."""
    return {
        "name": "edit_file",
        "description": """Use this tool to edit files on the system. When given a natural language command like 'change "Hello" to "Goodbye" in file.txt', this tool generates a string that contains:
    - The path to the file(s) to edit on its own line
    - The diff blocks to apply to the file(s)
    - IMPORTANT: the "SEARCH" portion needs to **exactly** match the original content in the file. 
    Note: this tool **cannot** be used to view files. Use the shell tool with commands like 'cat', 'head', 'tail', or 'less' for that.
    """,
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "LLM response containing path and diff blocks",
                }
            },
            "required": ["content"],
        },
    }
