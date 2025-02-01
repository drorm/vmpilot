#!/usr/bin/env python

from aider import models
from aider.io import InputOutput
from aider.coders.editblock_coder import EditBlockCoder, find_original_update_blocks
import logging
from pathlib import Path
from typing import Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AiderToolInput(BaseModel):
    """Input for the AiderTool"""

    path: str = Field(..., description="File to edit")
    content: str = Field(..., description="LLM response containing diff blocks")


class AiderTool(BaseTool):
    """VMPilot tool interface to aider's diff-based editing"""

    name: str = "edit_file"
    description: str = """Use this tool to edit files on the system. When given a natural language command like 'change "Hello" to "Goodbye" in file.txt', this tool will
    generate a diff of the changes and apply them to the file.
    Note: this tool **cannot** be used to view files. Use the bash tool with commands like 'cat', 'head', 'tail', or 'less' for that.
    """

    args_schema: Type[BaseModel] = AiderToolInput

    def _run(self, path: str, content: str) -> str:
        """
        Edit files using aider's diff format

        Args:
            path: File to edit
            content: LLM response containing diff blocks in the format:
            <<<<<<< SEARCH
            original content
            =======
            new content
            >>>>>>> REPLACE
        """
        try:

            replace = f"{path}\n{content}"
            # Use aider's built-in diff block parser
            edits = list(find_original_update_blocks(replace))
            logger.debug(edits)

            # Create EditBlockCoder instance
            io = InputOutput(line_endings="platform")
            main_model = models.Model(models.DEFAULT_MODEL_NAME)
            # We're passing the model, but it's not used in the EditBlockCoder. It's just a placeholder.
            editor = EditBlockCoder(main_model=main_model, io=io)

            editor.apply_edits(edits)
            return ""

        except Exception as e:
            logger.error(f"Error applying edits: {str(e)}")
            return f"Error: {str(e)}"

    async def _arun(self, path: str, content: str) -> str:
        """Async implementation of run"""
        logger.debug(f"_arun: path={path}, content={content}")
        return self._run(path, content)
