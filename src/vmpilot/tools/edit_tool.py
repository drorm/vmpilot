#!/usr/bin/env python
#
# This file uses concepts from the Aider project (https://github.com/Aider-AI/aider)
# which is licensed under the Apache License, Version 2.0

import logging
from pathlib import Path
from typing import Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from .edit_diff import do_replace, find_original_update_blocks

logger = logging.getLogger(__name__)


class AiderToolInput(BaseModel):
    """Using Aider battle-tested diff-based editing, edit files on the system"""

    content: str = Field(
        ..., description="LLM response containing path and diff blocks"
    )


class EditTool(BaseTool):
    """VMPilot tool interface to aider's diff-based editing"""

    name: str = "edit_file"
    description: str = """Use this tool to edit files on the system. When given a natural language command like 'change "Hello" to "Goodbye" in file.txt', this tool generates a string that contains:
    - The path to the file(s) to edit on its own line
    - The diff blocks to apply to the file(s)
    - IMPORTANT: the "SEARCH" portion needs to **exactly** match the original content in the file. 
    Note: this tool **cannot** be used to view files. Use the shell tool with commands like 'cat', 'head', 'tail', or 'less' for that.
    """

    args_schema: Type[BaseModel] = AiderToolInput

    def _run(self, content: str) -> str:
        """
        Edit files using aider's diff format

        Args:
            content:
            /path/to/file
            <<<<<<< SEARCH
            original content
            =======
            new content
            >>>>>>> REPLACE
        """
        try:
            # Use aider's built-in diff block parser to validate and extract edits
            edits = list(find_original_update_blocks(content))
            if not edits:
                raise ValueError("Invalid diff format")

            # Check if all files exist before proceeding
            for edit in edits:
                file_path = Path(
                    edit[0]
                )  # First element of edit tuple is the file path
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")

            # Apply the edits directly to the files
            for file_path, original, replacement in edits:
                with open(file_path, "r") as f:
                    content = f.read()
                new_content = do_replace(file_path, content, original, replacement)
                if new_content is not None:
                    with open(file_path, "w") as f:
                        f.write(new_content)
                else:
                    return "No matches found"
            return f"\n\n**Edited {file_path}.**\n\n"

        except FileNotFoundError:
            raise
        except ValueError:
            logger.info(f"Error value in edit {content}")
            raise

    async def _arun(self, content: str) -> str:
        """Async implementation of run"""
        logger.debug(f"_arun: content={content}")
        return self._run(content)
