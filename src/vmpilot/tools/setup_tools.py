"""
Initialize and configure the tools we use as described in the prompt.
"""

import logging
import traceback
import warnings

from vmpilot.config import google_search_config
from vmpilot.setup_shell import SetupShellTool
from vmpilot.tools.create_file import CreateFileTool
from vmpilot.tools.edit_tool import EditTool
from vmpilot.tools.google_search_tool import GoogleSearchTool
from vmpilot.tools.searchtool import SearchTool

# Configure logging
logger = logging.getLogger(__name__)


def is_google_search_enabled() -> bool:
    """Check if Google Search is enabled by verifying configuration and environment variables."""
    if not google_search_config.enabled:
        logger.debug("Google Search is disabled in configuration")
        return False

    if not google_search_config.is_properly_configured():
        logger.info(
            f"Google Search is enabled in configuration but required environment variables "
            f"({google_search_config.api_key_env} and/or {google_search_config.cse_id_env}) are missing"
        )
        return False

    return True


def get_google_search_status() -> str:
    """Get a human-readable status message for Google Search configuration."""
    if not google_search_config.enabled:
        return "Google Search is disabled in configuration"

    import os

    missing_vars = []
    if not os.getenv(google_search_config.api_key_env):
        missing_vars.append(google_search_config.api_key_env)
    if not os.getenv(google_search_config.cse_id_env):
        missing_vars.append(google_search_config.cse_id_env)

    if missing_vars:
        return f"Google Search is enabled in configuration but missing environment variables: {', '.join(missing_vars)}"

    return "Google Search is enabled and properly configured"


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
            tools.append(SearchTool())  # for code search

            # Conditionally add Google Search tool if enabled
            if is_google_search_enabled():
                try:
                    search_tool = GoogleSearchTool()
                    if search_tool.is_configured:
                        tools.append(search_tool)
                        logger.debug("Google Search Tool added to available tools")
                    else:
                        logger.warning(
                            "Google Search Tool initialization failed, not adding to tools"
                        )
                except Exception as e:
                    logger.error(f"Error creating Google Search Tool: {e}")
                    logger.error("".join(traceback.format_tb(e.__traceback__)))
            else:
                if google_search_config.enabled:
                    import os

                    missing_vars = []
                    if not os.getenv(google_search_config.api_key_env):
                        missing_vars.append(google_search_config.api_key_env)
                    if not os.getenv(google_search_config.cse_id_env):
                        missing_vars.append(google_search_config.cse_id_env)

                    logger.warning(
                        "Google Search is enabled in configuration but environment variables are missing. "
                        f"Please set: {', '.join(missing_vars)}"
                    )
                else:
                    logger.debug(
                        "Google Search Tool not enabled in configuration, skipping"
                    )

        except Exception as e:
            logger.error(f"Error: Error creating tools: {e}")
            logger.error("".join(traceback.format_tb(e.__traceback__)))

    # Return all tools
    return tools
