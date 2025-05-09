import logging
import os
from typing import Any, Dict, Optional, Type

from langchain_core.tools import BaseTool
from langchain_google_community.search import GoogleSearchAPIWrapper
from pydantic import BaseModel, Field

from vmpilot.config import google_search_config

# Hide Google API client message: googleapiclient.discovery_cache - INFO - file_cache is only supported with oauth2client<4.0.0
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


class Input(BaseModel):
    """Input schema for Google search."""

    query: str = Field(description="The search query to execute")
    num_results: int = Field(
        description="Number of results to return (default: 10)", default=10
    )


class GoogleSearchTool(BaseTool):
    """Execute Google searches."""

    name: str = "google_search"
    description: str = """Search Google for information. Input should be a search query string. Examples:
            - "latest news about Python"
            - "how to implement OAuth2"
            - "weather in San Francisco"
            The output will be a list of relevant search results."""
    args_schema: Type[BaseModel] = Input
    search: Optional[GoogleSearchAPIWrapper] = None
    is_configured: bool = False

    def __init__(self, **kwargs):
        """Initialize the Google Search tool."""
        super().__init__(**kwargs)

        # Check if tool is enabled in configuration
        if not google_search_config.enabled:
            logger.info("Google Search Tool is disabled in configuration")
            self.is_configured = False
            self.search = None
            return

        # Check if required environment variables are set
        google_api_key = os.getenv(google_search_config.api_key_env)
        google_cse_id = os.getenv(google_search_config.cse_id_env)

        if not google_api_key or not google_cse_id:
            logger.warning(
                "Google Search Tool is not properly configured. "
                "Missing required environment variables: "
                f"{google_search_config.api_key_env if not google_api_key else ''}"
                f"{' and ' if not google_api_key and not google_cse_id else ''}"
                f"{google_search_config.cse_id_env if not google_cse_id else ''}"
            )
            self.is_configured = False
            self.search = None
            return

        # Initialize the Google Search wrapper
        try:
            self.search = GoogleSearchAPIWrapper(
                google_api_key=google_api_key,
                google_cse_id=google_cse_id,
                k=google_search_config.max_results,
            )
            self.is_configured = True
            logger.info("Google Search Tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Search Tool: {str(e)}")
            self.is_configured = False
            self.search = None

    def _run(
        self,
        query: str,
        num_results: int = 10,
    ) -> str:
        """Execute Google search."""
        # Check if the search tool is configured
        if not self.is_configured or self.search is None:
            if not google_search_config.enabled:
                return (
                    "Google Search is disabled in configuration. "
                    "To enable it, set 'enabled = true' in the [google_search] section of config.ini."
                )
            else:
                import os

                missing_vars = []
                if not os.getenv(google_search_config.api_key_env):
                    missing_vars.append(google_search_config.api_key_env)
                if not os.getenv(google_search_config.cse_id_env):
                    missing_vars.append(google_search_config.cse_id_env)

                return (
                    "Google Search API is not properly configured. "
                    f"The following environment variables are missing: {', '.join(missing_vars)}. "
                    "Please set these variables to use Google Search."
                )

        try:
            # Perform the search
            results = self.search.results(query, num_results)

            # Format the results
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                link = result.get("link", "No link")
                snippet = result.get("snippet", "No description")

                formatted_results.append(f"{i}. **{title}**\n   {snippet}\n   {link}\n")

            if not formatted_results:
                return "No results found for your query."

            formatted_results = "\n".join(formatted_results)
            formatted_results = f"\n````markdown\n{formatted_results}\n````\n\n"
            return formatted_results

        except ConnectionError as e:
            logger.error(f"Connection error during Google search: {str(e)}")
            return f"Error: Could not connect to Google Search API. Please check your internet connection. Details: {str(e)}"
        except ValueError as e:
            logger.error(f"Value error during Google search: {str(e)}")
            return f"Error: Invalid search parameters. Details: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during Google search: {str(e)}")
            return f"Error performing search: {str(e)}"

    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to execute",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 4)",
                        "default": 4,
                    },
                },
                "required": ["query"],
            },
        }
