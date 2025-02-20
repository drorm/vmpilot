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
    description: str = """
Use this tool when you need to replace specific text in a file on the system. The user’s instructions will generally look like:
“Change ‘old text’ to ‘new text’ in `/path/to/file.ext`.”
or
“Replace <original snippet> with <new snippet> in `/path/to/anotherFile.py`.”

**Output Format**
The tool expects a *single structured response* with exactly six segments, in this order:
1. **Line 1:** The absolute path to the file to edit.
2. **Line 2:** The literal string `<<<<<<< SEARCH`
3. **Lines 3..(n-2):** The exact original content to search for in the file. This can span *one or more lines* (e.g., multiple lines of code).
4. **Next Line (n-1):** The literal string `=======`
5. **Lines (n..m-1):** The replacement content—i.e., the text we want to use instead. This can also be *one or more lines* as needed.
6. **Last line (m):** The literal string `>>>>>> REPLACE`

**Important Details**
1. **File Path:** - Always use the file path specified by the user. Do not assume or switch to a default path unless explicitly provided.
2. **Exact Match on ‘SEARCH’ Block:** - The content between `<<<<<<< SEARCH` and `=======` must match *exactly* the original text in the file (including whitespace, punctuation, and line breaks).
3. **Replacement Content:** - Under `=======`, include *all* lines of the updated text.
4. **No Extra Lines or Characters:** - Do not prepend or append lines, white space, or extra text in the generated output—only what’s strictly in the original snippet plus the requested replacement.

**Example**
If the request is _“Replace the two lines
```
console.log("Hello, world!");
console.log("Another line!");
```
with
```
console.log("New line 1");
console.log("New line 2");
```
in `/tmp/index.js`,”_ your output should look like:

```
/tmp/index.js
<<<<<<< SEARCH
console.log("Hello, world!");
console.log("Another line!");
=======
console.log("New line 1");
console.log("New line 2");
>>>>>> REPLACE
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
