"""
Initialize and configure the tools we use as described in the prompt.
"""

import logging
import traceback
import warnings

from vmpilot.setup_shell import SetupShellTool
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
            shell_tool = SetupShellTool()
            tools.append(shell_tool)
            tools.append(EditTool())  # for editing
            tools.append(CreateFileTool())  # for creating files
        except Exception as e:
            logger.error(f"Error: Error creating tool: {e}")
            logger.error("".join(traceback.format_tb(e.__traceback__)))

    # Return all tools
    return tools
