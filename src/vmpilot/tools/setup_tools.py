"""
Initialize and configure the tools we use as described in the prompt.
"""

import logging
import os
import traceback
import warnings

from vmpilot.setup_shell import SetupShellTool
from vmpilot.tools.create_file import CreateFileTool
from vmpilot.tools.edit_tool import EditTool
from vmpilot.tools.google_search_tool import GoogleSearchTool

# Configure logging
logger = logging.getLogger(__name__)


def is_google_search_enabled() -> bool:
    """Check if Google Search is enabled by verifying required environment variables."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")

    if not google_api_key or not google_cse_id:
        logger.info(
            "Google Search is disabled. Missing required environment variables: "
            f"{'GOOGLE_API_KEY' if not google_api_key else ''}"
            f"{' and ' if not google_api_key and not google_cse_id else ''}"
            f"{'GOOGLE_CSE_ID' if not google_cse_id else ''}"
        )
        return False

    return True


def setup_tools(llm=None):
    # Suppress warning about shell tool safeguards
    warnings.filterwarnings(
        "ignore", category=UserWarning, module="langchain_community.tools.shell.tool"
    )

    tools = []

    if llm is not None:
        try:
            # Add core tools
            shell_tool = SetupShellTool()
            tools.append(shell_tool)
            tools.append(EditTool())  # for editing
            tools.append(CreateFileTool())  # for creating files

            # Conditionally add Google Search tool if enabled
            if is_google_search_enabled():
                try:
                    search_tool = GoogleSearchTool()
                    if search_tool.is_configured:
                        tools.append(search_tool)
                        logger.info("Google Search Tool added to available tools")
                    else:
                        logger.warning(
                            "Google Search Tool initialization failed, not adding to tools"
                        )
                except Exception as e:
                    logger.error(f"Error creating Google Search Tool: {e}")
                    logger.error("".join(traceback.format_tb(e.__traceback__)))
            else:
                logger.info("Google Search Tool not enabled, skipping")

        except Exception as e:
            logger.error(f"Error: Error creating tools: {e}")
            logger.error("".join(traceback.format_tb(e.__traceback__)))

    # Return all tools
    return tools
