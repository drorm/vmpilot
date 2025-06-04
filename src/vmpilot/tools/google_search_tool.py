import logging
import os
from typing import Any, Dict

import requests

from vmpilot.config import google_search_config

# Hide Google API client message: googleapiclient.discovery_cache - INFO - file_cache is only supported with oauth2client<4.0.0
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


def google_search_executor(args: Dict[str, Any]) -> str:
    """
    LiteLLM-compatible executor function for Google search.

    Args:
        args: Dictionary containing 'query' and optional 'num_results' keys

    Returns:
        Search results as formatted string
    """
    query = args.get("query")
    num_results = args.get("num_results", 10)

    if not query:
        return "Error: No search query provided"

    # Create GoogleSearchTool instance and execute search
    search_tool = GoogleSearchTool()
    return search_tool._run(query, num_results)


class GoogleSearchTool:
    """Execute Google searches."""

    name: str = "google_search"
    description: str = """Search Google for information. Input should be a search query string. Examples:
            - "latest news about Python"
            - "how to implement OAuth2"
            - "weather in San Francisco"
            The output will be a list of relevant search results."""
    is_configured: bool = False

    def __init__(self):
        """Initialize the Google Search tool."""
        # Check if tool is enabled in configuration
        if not google_search_config.enabled:
            logger.info("Google Search Tool is disabled in configuration")
            self.is_configured = False
            return

        # Check if required environment variables are set
        self.google_api_key = os.getenv(google_search_config.api_key_env)
        self.google_cse_id = os.getenv(google_search_config.cse_id_env)

        if not self.google_api_key or not self.google_cse_id:
            logger.warning(
                "Google Search Tool is not properly configured. "
                "Missing required environment variables: "
                f"{google_search_config.api_key_env if not self.google_api_key else ''}"
                f"{' and ' if not self.google_api_key and not self.google_cse_id else ''}"
                f"{google_search_config.cse_id_env if not self.google_cse_id else ''}"
            )
            self.is_configured = False
            return

        self.is_configured = True
        logger.debug("Google Search Tool initialized successfully")

    def _run(
        self,
        query: str,
        num_results: int = 10,
    ) -> str:
        """Execute Google search."""
        # Check if the search tool is configured
        if not self.is_configured:
            if not google_search_config.enabled:
                return (
                    "Google Search is disabled in configuration. "
                    "To enable it, set 'enabled = true' in the [google_search] section of config.ini."
                )
            else:
                missing_vars = []
                if not self.google_api_key:
                    missing_vars.append(google_search_config.api_key_env)
                if not self.google_cse_id:
                    missing_vars.append(google_search_config.cse_id_env)

                return (
                    "Google Search API is not properly configured. "
                    f"The following environment variables are missing: {', '.join(missing_vars)}. "
                    "Please set these variables to use Google Search."
                )

        try:
            # Perform the search using Google Custom Search API
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cse_id,
                "q": query,
                "num": min(
                    num_results, 10
                ),  # Google API limits to 10 results per request
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            # Format the results
            formatted_results = []
            for i, item in enumerate(items, 1):
                title = item.get("title", "No title")
                link = item.get("link", "No link")
                snippet = item.get("snippet", "No description")

                formatted_results.append(f"{i}. **{title}**\n   {snippet}\n   {link}\n")

            if not formatted_results:
                return "No results found for your query."

            formatted_results = "\n".join(formatted_results)
            formatted_results = f"\n````markdown\n{formatted_results}\n````\n\n"
            return formatted_results

        except requests.ConnectionError as e:
            logger.error(f"Connection error during Google search: {str(e)}")
            return f"Error: Could not connect to Google Search API. Please check your internet connection. Details: {str(e)}"
        except requests.HTTPError as e:
            logger.error(f"HTTP error during Google search: {str(e)}")
            return f"Error: HTTP error from Google Search API. Details: {str(e)}"
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
