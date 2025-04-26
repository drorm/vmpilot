#!/usr/bin/env python
"""
Build the code index for the RAG-based code retrieval system.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Use a direct relative import to avoid module path issues
from .indexer import create_code_index

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the index builder."""
    parser = argparse.ArgumentParser(
        description="Build a code index for the VMPilot RAG system"
    )
    parser.add_argument(
        "source_dir",
        help="Directory containing source code to index",
    )
    parser.add_argument(
        "--vector-store-dir",
        default=os.path.expanduser("~/.vmpilot/code_index"),
        help="Directory to store the vector index (default: ~/.vmpilot/code_index)",
    )
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-small",
        help="Name of the embedding model to use (default: text-embedding-3-small)",
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["python"],
        help="Programming languages to support (default: python)",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".py", ".md", ".txt", ".json", ".yaml", ".yml"],
        help="File extensions to index (default: .py .md .txt .json .yaml .yml)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Maximum size of code chunks (default: 1000)",
    )
    parser.add_argument(
        "--chunk_lines_overlap",
        type=int,
        default=200,
        help="Overlap between consecutive chunks (default: 200)",
    )

    args = parser.parse_args()

    # Validate source directory
    source_path = Path(args.source_dir)
    if not source_path.exists():
        logger.error(f"Source directory {args.source_dir} does not exist")
        sys.exit(1)

    # Create vector store directory if it doesn't exist
    vector_store_path = Path(args.vector_store_dir)
    vector_store_path.mkdir(parents=True, exist_ok=True)

    # Build the index
    logger.info(f"Building code index from {args.source_dir}")
    logger.info(f"Vector store will be saved to {args.vector_store_dir}")

    try:
        create_code_index(
            source_dir=str(source_path),
            vector_store_dir=str(vector_store_path),
            embedding_model=args.embedding_model,
            file_extensions=args.extensions,
            languages=args.languages,
            chunk_lines=args.chunk_lines,
            chunk_lines_overlap=args.chunk_lines_overlap,
        )
        logger.info("Index built successfully")
    except Exception as e:
        logger.error(f"Error building index: {str(e)}")
        # show the traceback
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
