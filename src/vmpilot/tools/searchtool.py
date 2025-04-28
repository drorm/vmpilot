"""Tool for searching code within a project using natural language queries."""

import logging
import os

# Import the code search functionality from the standalone module
# These imports assume the codesearch module is in the Python path
# If not, you may need to add it dynamically
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

sys.path.append(str(Path(__file__).parent.parent.parent))
try:
    from codesearch.search import search_project_code
    from codesearch.utils import load_config
except ImportError:
    from src.codesearch.search import search_project_code
    from src.codesearch.utils import load_config

logger = logging.getLogger(__name__)


class SearchInput(BaseModel):
    """Input schema for code search."""

    query: str = Field(
        description="The natural language query to search for in the codebase"
    )
    project_root: str = Field(
        default=None,
        description="Root directory of the project to search (defaults to current directory)",
    )
    config_path: str = Field(
        default=None,
        description="Path to the search configuration file (defaults to searchconfig.yaml in codesearch directory)",
    )
    output_format: str = Field(
        default="markdown", description="Output format: markdown, json, or text"
    )
    verbose: bool = Field(default=False, description="Enable verbose logging")
    model: str = Field(
        default=None,
        description="LLM model to use for search (defaults to config file setting)",
    )


class SearchTool(BaseTool):
    """Tool for searching code using natural language queries."""

    name: str = "search_code"
    description: str = """Search code in a project using natural language queries.
    Examples:
    - "Find all functions that handle user authentication"
    - "How does the error handling work in the API routes?"
    - "Where is the database connection configured?"
    - "Find code that processes file uploads"
    
    Results include relevant files, code snippets, and explanations.
    """
    args_schema: Type[BaseModel] = SearchInput

    def _run(
        self,
        query: str,
        project_root: Optional[str] = None,
        config_path: Optional[str] = None,
        output_format: str = "markdown",
        verbose: bool = False,
        model: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute code search and return formatted results."""
        try:
            # Set up project root
            if project_root is None:
                project_root = os.getcwd()

            # Set up config path
            if config_path is None:
                # Use the default config in the codesearch directory
                module_dir = Path(__file__).parent.parent.parent / "codesearch"
                config_path = str(module_dir / "searchconfig.yaml")

            # Configure logging level
            if verbose:
                logger.setLevel(logging.DEBUG)

            # Call the search function from the standalone module
            result = search_project_code(
                query=query,
                project_root=project_root,
                config_path=config_path,
                output_format=output_format,
                model=model,
            )

            return result

        except Exception as e:
            logger.error(f"Error executing code search for query '{query}': {str(e)}")
            return f"Error searching code: {str(e)}"

    async def _arun(
        self,
        query: str,
        project_root: Optional[str] = None,
        config_path: Optional[str] = None,
        output_format: str = "markdown",
        verbose: bool = False,
        model: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Run the code search asynchronously."""
        return self._run(
            query=query,
            project_root=project_root,
            config_path=config_path,
            output_format=output_format,
            verbose=verbose,
            model=model,
            run_manager=run_manager,
        )
