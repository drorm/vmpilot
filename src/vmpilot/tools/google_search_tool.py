import logging
import os
from typing import Any, Dict, Optional, Type

from langchain_core.tools import BaseTool
from langchain_google_community.search import GoogleSearchAPIWrapper
from pydantic import BaseModel, Field

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

        # Check if required environment variables are set
        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_cse_id = os.getenv("GOOGLE_CSE_ID")

        if not google_api_key or not google_cse_id:
            logger.warning(
                "Google Search Tool is not properly configured. "
                "Missing required environment variables: "
                f"{'GOOGLE_API_KEY' if not google_api_key else ''}"
                f"{' and ' if not google_api_key and not google_cse_id else ''}"
                f"{'GOOGLE_CSE_ID' if not google_cse_id else ''}"
            )
            self.is_configured = False
            self.search = None
            return

        # Initialize the Google Search wrapper
        try:
            self.search = GoogleSearchAPIWrapper(
                google_api_key=google_api_key,
                google_cse_id=google_cse_id,
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
            return (
                "Google Search API is not properly configured. "
                "Please check if GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables are set."
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

                formatted_results.append(
                    f"{i}. **{title}**\n   {snippet}\n   URL: {link}\n"
                )

            if not formatted_results:
                return "No results found for your query."

            formatted_results = "\n".join(formatted_results)
            formatted_results = f"\n````{formatted_results}\n````\n\n"
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
