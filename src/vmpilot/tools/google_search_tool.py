import logging
import os
from typing import Any, Dict, List, Optional, Type, Union

from langchain_core.tools import BaseTool
from langchain_google_community.search import GoogleSearchAPIWrapper
from pydantic import BaseModel, Field, model_validator

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
    search: GoogleSearchAPIWrapper = None

    def __init__(self, **kwargs):
        """Initialize the Google Search tool."""
        super().__init__(**kwargs)
        # Initialize the Google Search wrapper
        self.search = GoogleSearchAPIWrapper(
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            google_cse_id=os.getenv("GOOGLE_CSE_ID"),
        )

    def _run(
        self,
        query: str,
        num_results: int = 10,
    ) -> str:
        """Execute Google search."""
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
                return "No results found."

            formatted_results = "\n".join(formatted_results)
            formatted_results = f"\n````{formatted_results}\n````\n\n"
            return formatted_results

        except Exception as e:
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
