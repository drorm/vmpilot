"""
Initialize and configure the tools we use as described in the prompt.
"""

import logging
import os
import traceback
import warnings
from pathlib import Path

from vmpilot.setup_shell import SetupShellTool
from vmpilot.tools.code_retrieval_tool import CodeRetrievalTool
from vmpilot.tools.create_file import CreateFileTool
from vmpilot.tools.edit_tool import EditTool

# Configure logging
logger = logging.getLogger(__name__)


def setup_tools(llm=None):
    # Suppress warning about shell tool safeguards
    warnings.filterwarnings(
        "ignore", category=UserWarning, module="langchain_community.tools.shell.tool"
    )

    tools = []

    if llm is not None:
        try:
            # Add standard tools
            shell_tool = SetupShellTool()
            tools.append(shell_tool)
            tools.append(EditTool())  # for editing
            tools.append(CreateFileTool())  # for creating files

            # Add code retrieval tool if the index exists
            vector_store_dir = os.path.expanduser("~/.vmpilot/code_index")
            if Path(vector_store_dir).exists():
                try:
                    code_retrieval_tool = CodeRetrievalTool(
                        vector_store_dir=vector_store_dir,
                    )
                    tools.append(code_retrieval_tool)
                    logger.info("Code retrieval tool initialized successfully")
                except Exception as e:
                    logger.warning(f"Could not initialize code retrieval tool: {e}")
                    logger.error("".join(traceback.format_tb(e.__traceback__)))
            else:
                logger.info(
                    "Code index not found at %s. Code retrieval tool not available.",
                    vector_store_dir,
                )
        except Exception as e:
            logger.error(f"Error: Error creating tool: {e}")
            logger.error("".join(traceback.format_tb(e.__traceback__)))

    # Return all tools
    return tools
