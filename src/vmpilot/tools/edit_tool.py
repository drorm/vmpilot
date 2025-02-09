#!/usr/bin/env python

import logging
from pathlib import Path
from typing import Optional, Type

from aider import models
from aider.coders.editblock_coder import EditBlockCoder, find_original_update_blocks
from aider.io import InputOutput
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

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
    Note: this tool **cannot** be used to view files. Use the bash tool with commands like 'cat', 'head', 'tail', or 'less' for that.
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

            # Create EditBlockCoder instance
            io = InputOutput(line_endings="platform")
            main_model = models.Model(models.DEFAULT_MODEL_NAME)
            editor = EditBlockCoder(main_model=main_model, io=io)

            try:
                editor.apply_edits(edits)
                return ""
            except ValueError as e:
                if "SearchReplaceNoExactMatch" in str(e):
                    return "No matches found"
                raise
            except Exception as e:
                error_message = f"Error: \n```\n{str(e)}\n```\n"
                return error_message

        except FileNotFoundError:
            raise
        except ValueError:
            raise

    async def _arun(self, content: str) -> str:
        """Async implementation of run"""
        logger.debug(f"_arun: content={content}")
        return self._run(content)
