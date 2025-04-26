"""Tool for retrieving code context using hybrid RAG."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from vmpilot.ragcode.retriever import CodeRetriever

logger = logging.getLogger(__name__)


class CodeRetrievalInput(BaseModel):
    """Input schema for code retrieval."""

    query: str = Field(description="Query to find relevant code")
    file_path: Optional[str] = Field(
        default=None, description="Optional file path to limit the search"
    )
    language: Optional[str] = Field(
        default=None, description="Optional programming language to filter by"
    )
    top_k: int = Field(default=3, description="Number of code chunks to retrieve")


class CodeRetrievalTool(BaseTool):
    """Tool for retrieving code context using hybrid RAG."""

    name: str = "code_retrieval"
    description: str = """
    Retrieve relevant code chunks based on semantic search. This tool helps you find code definitions, 
    implementations, and documentation across the codebase without needing to know exact file locations.
    
    Examples:
    - Find implementation of the ShellTool class
    - Show how configuration is loaded in the project
    - Find code related to agent initialization
    - Look for functions that handle GitHub issues
    
    The tool returns code chunks with their file locations and relevance scores.
    """
    args_schema: Type[BaseModel] = CodeRetrievalInput
    retriever: Optional[Any] = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)

    def __init__(
        self,
        vector_store_dir: str = "~/.vmpilot/code_index",
        embedding_model: str = "text-embedding-3-small",
        **kwargs,
    ):
        """
        Initialize the code retrieval tool.

        Args:
            vector_store_dir: Directory containing the vector store
            embedding_model: Name of the embedding model to use
        """
        super().__init__(**kwargs)

        # Initialize the retriever
        vector_store_path = Path(vector_store_dir)
        if vector_store_path.exists():
            self.retriever = CodeRetriever(
                vector_store_dir=str(vector_store_path),
                embedding_model=embedding_model,
            )
            self.is_initialized = True
        else:
            logger.warning(
                f"Vector store directory {vector_store_dir} does not exist. "
                "The tool will not be able to retrieve code until the index is created."
            )
            self.is_initialized = False
            self.retriever = None

    def _run(
        self,
        query: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        top_k: int = 3,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Execute code retrieval and return formatted results.

        Args:
            query: Query to find relevant code
            file_path: Optional file path to limit the search
            language: Optional programming language to filter by
            top_k: Number of code chunks to retrieve
            run_manager: Callback manager

        Returns:
            Formatted string with code chunks and metadata
        """
        if not self.is_initialized:
            return (
                "⚠️ Code index not found. Please run the indexing command first:\n"
                "```bash\n"
                "python -m vmpilot.ragcode.indexer <source_dir> <vector_store_dir>\n"
                "```"
            )

        # Prepare context for the query
        context = {}
        if file_path:
            context["file_path"] = file_path
        if language:
            context["language"] = language

        # Retrieve code chunks
        try:
            results = self.retriever.retrieve(query, context)

            # Limit results if needed
            results = results[:top_k]

            if not results:
                return f"No code found matching query: {query}"

            # Format results
            formatted_results = f"**Results for query: {query}**\n\n"

            for i, result in enumerate(results, 1):
                content = result["content"]
                metadata = result["metadata"]
                score = result.get("score", 0.0)
                structure_info = result.get("structure_info", {})

                file_path = metadata.get("file_path", "Unknown file")
                language = metadata.get("language", "text")

                # Get a more descriptive title based on structure info
                title = os.path.basename(file_path)
                if structure_info:
                    if "name" in structure_info and "type" in structure_info:
                        title = f"{structure_info['type']} `{structure_info['name']}` in {title}"

                # Format the code block with enhanced information
                formatted_results += f"### Result {i}: {title} (Score: {score:.2f})\n"
                formatted_results += f"**Path:** {file_path}\n"

                # Add structure information if available
                if structure_info:
                    if "description" in structure_info:
                        formatted_results += (
                            f"**Description:** {structure_info['description']}\n"
                        )
                    if (
                        "parent_classes" in structure_info
                        and structure_info["parent_classes"]
                    ):
                        formatted_results += (
                            f"**Inherits from:** `{structure_info['parent_classes']}`\n"
                        )

                # Add imports if available
                if "imports" in metadata:
                    formatted_results += f"**Imports:** `{metadata['imports']}`\n"

                formatted_results += f"\n```{language}\n{content}\n```\n\n"

            return formatted_results

        except Exception as e:
            logger.error(f"Error retrieving code for query '{query}': {str(e)}")
            return f"Error retrieving code: {str(e)}"

    async def _arun(
        self,
        query: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        top_k: int = 3,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Run the code retrieval asynchronously."""
        return self._run(
            query=query,
            file_path=file_path,
            language=language,
            top_k=top_k,
            run_manager=run_manager,
        )
