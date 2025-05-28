"""
Initialize and configure the tools we use as described in the prompt.
"""

import logging
import traceback

from vmpilot.config import google_search_config
from vmpilot.tools.create_file import create_file_executor, get_create_file_schema
from vmpilot.tools.edit_tool import edit_file_executor, get_edit_file_schema
from vmpilot.tools.google_search_tool import GoogleSearchTool, google_search_executor
from vmpilot.tools.shelltool import execute_shell_command, shell_tool

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
        missing_vars.append(str(google_search_config.api_key_env))
    if not os.getenv(google_search_config.cse_id_env):
        missing_vars.append(str(google_search_config.cse_id_env))

    if missing_vars:
        return f"Google Search is enabled in configuration but missing environment variables: {', '.join(missing_vars)}"

    return "Google Search is enabled and properly configured"


def setup_tools(model: str | None = None):
    """Set up the tools used by the agent."""
    tools = []

    # Always add the core shell tool
    # shell_tool is already in the correct format with "type": "function"
    tools.append({"schema": shell_tool, "executor": execute_shell_command})

    # Add create_file tool
    create_file_schema = {"type": "function", "function": get_create_file_schema()}
    tools.append({"schema": create_file_schema, "executor": create_file_executor})

    # Add edit_file tool
    edit_file_schema = {"type": "function", "function": get_edit_file_schema()}
    tools.append({"schema": edit_file_schema, "executor": edit_file_executor})

    # Add Claude web search tool if using Claude model
    # is_claude_model or claude_web_search_executor may not be defined, so skip this if not present
    try:
        if model and "is_claude_model" in globals() and is_claude_model(model):
            claude_search_schema = {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5,
            }
            tools.append(
                {"schema": claude_search_schema, "executor": claude_web_search_executor}
            )
            logger.debug("Claude web search tool added to available tools")
    except Exception:
        pass

    # Add Gemini search tool if using Gemini model
    try:
        if model and is_gemini_model(model):
            gemini_search_schema = {"googleSearch": {}}
            tools.append(
                {"schema": gemini_search_schema, "executor": gemini_search_executor}
            )
            logger.debug("Gemini search tool added to available tools")
    except Exception:
        pass

    # Note: Gemini native search tool is not needed since Google Search tool works fine with Gemini
    # and mixing native tools with function calling tools causes "Tool use with function calling is unsupported" error

    # Conditionally add Google Search tool if enabled
    try:
        if is_google_search_enabled():
            try:
                # Create Google Search tool and ensure it has the right format for LiteLLM
                search_tool = GoogleSearchTool()
                if getattr(search_tool, "is_configured", False):
                    # Get the schema using the get_schema method
                    if hasattr(search_tool, "get_schema") and callable(
                        search_tool.get_schema
                    ):
                        schema = search_tool.get_schema()
                        # Format for LiteLLM compatibility
                        # The schema should already have the name, description, and parameters
                        litellm_schema = {"type": "function", "function": schema}
                        tools.append(
                            {
                                "schema": litellm_schema,
                                "executor": google_search_executor,
                            }
                        )
                        logger.debug("Google Search Tool added to available tools")
                    else:
                        logger.debug(
                            "Google Search Tool doesn't have the required get_schema method"
                        )
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
        logger.error(f"Error creating tools: {e}")
        logger.error("".join(traceback.format_tb(e.__traceback__)))

    # Return all tools
    return tools


def is_claude_model(model: str) -> bool:
    """Check if the model is a Claude model."""
    if not model:
        return False
    return "claude" in model.lower() or "anthropic" in model.lower()


def is_gemini_model(model: str) -> bool:
    """Check if the model is a Gemini model."""
    if not model:
        return False
    return "gemini" in model.lower() or model.lower().startswith("gemini-")


def claude_web_search_executor(tool_args: dict) -> str:
    """
    Executor for Claude's web search tool.

    Note: This is a placeholder executor since Claude's web search is handled
    natively by the model. This function should not be called in practice,
    but is included for completeness.
    """
    query = tool_args.get("query", "")
    logger.error(f"Claude web search called with query: {query}")
    return f"Claude web search executed for query: {query}"


def gemini_search_executor(tool_args: dict) -> str:
    """
    Executor for Gemini's search tool.

    Note: This is a placeholder executor since Gemini's search is handled
    natively by the model. This function should not be called in practice,
    but is included for completeness.
    """
    query = tool_args.get("query", "")
    logger.error(f"Gemini search called with query: {query}")
    return f"Gemini search executed for query: {query}"


def is_gemini_model(model: str) -> bool:
    """Check if the model is a Gemini model."""
    if not model:
        return False
    return "gemini" in model.lower() or model.lower().startswith("gemini-")


def gemini_search_executor(tool_args: dict) -> str:
    """
    Executor for Gemini's search tool.

    Note: This is a placeholder executor since Gemini's search is handled
    natively by the model. This function should not be called in practice,
    but is included for completeness.
    """
    query = tool_args.get("query", "")
    logger.error(f"Gemini search called with query: {query}")
    return f"Gemini search executed for query: {query}"
