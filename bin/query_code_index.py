#!/usr/bin/env python
"""
Command-line script for querying the code index.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_dir = os.path.join(project_root, "src")
sys.path.insert(0, src_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Check for Chroma dependencies
try:
    import chromadb
    from llama_index.vector_stores.chroma import ChromaVectorStore

    logger.info("Successfully imported Chroma dependencies")
    HAS_CHROMA = True
except ImportError as e:
    logger.warning(f"Chroma dependencies not found: {e}")
    logger.warning(
        "For best performance, install: pip install llama-index-vector-stores-chroma chromadb"
    )
    HAS_CHROMA = False

# Import the CodeRetriever
try:
    from vmpilot.ragcode.retriever import CodeRetriever

    logger.info("Successfully imported CodeRetriever from vmpilot.ragcode.retriever")
except ImportError as e:
    # Try the old location as fallback
    try:
        from ragcode.retriever import CodeRetriever

        logger.info(
            "Successfully imported CodeRetriever from ragcode.retriever (old location)"
        )
    except ImportError:
        logger.error(f"Failed to import CodeRetriever: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Query the code index")
    parser.add_argument("query", help="Query to find relevant code")
    parser.add_argument("--file-path", help="Optional file path to limit the search")
    parser.add_argument("--language", help="Optional programming language to filter by")
    parser.add_argument(
        "--top-k", type=int, default=3, help="Number of code chunks to retrieve"
    )
    parser.add_argument(
        "--vector-store-dir",
        default=os.path.expanduser("~/.vmpilot/code_index"),
        help="Directory containing the vector store",
    )
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-small",
        help="Name of the embedding model to use",
    )

    args = parser.parse_args()

    # Initialize the retriever
    try:
        # Inform user about Chroma status
        if HAS_CHROMA:
            logger.info("Using Chroma vector store for improved performance")
        else:
            logger.warning("Using fallback vector store (Chroma not available)")

        retriever = CodeRetriever(
            vector_store_dir=args.vector_store_dir,
            embedding_model=args.embedding_model,
        )
    except Exception as e:
        logger.error(f"Failed to initialize CodeRetriever: {e}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)

    # Prepare context for the query
    context = {}
    if args.file_path:
        context["file_path"] = args.file_path
    if args.language:
        context["language"] = args.language

    # Retrieve code chunks
    try:
        results = retriever.retrieve(args.query, context)

        # Limit results if needed
        results = results[: args.top_k]

        if not results:
            print(f"No results found for query: {args.query}")
            return

        # Print results
        print(f"\nResults for query: {args.query}\n")

        for i, result in enumerate(results, 1):
            content = result["content"]
            metadata = result["metadata"]
            score = result.get("score", 0.0)

            file_path = metadata.get("file_path", "Unknown file")
            language = metadata.get("language", "text")

            print(f"Result {i}: {os.path.basename(file_path)} (Score: {score:.2f})")
            print(f"Path: {file_path}\n")
            print(f"```{language}")
            print(content)
            print("```\n")
    except Exception as e:
        logger.error(f"Error retrieving results: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
