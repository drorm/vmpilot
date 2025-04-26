"""
RAG-based code retrieval system for VMPilot.
Provides structure-aware code indexing and hybrid retrieval capabilities.

Dependencies:
- llama-index>=0.10.7
- llama-index-core>=0.10.7
- llama-index-embeddings-openai>=0.1.5
- llama-index-vector-stores-chroma>=0.1.1
- chromadb>=0.4.18
- tree-sitter>=0.20.1
"""

# Check for required dependencies
try:
    import chromadb
    from llama_index.vector_stores.chroma import ChromaVectorStore

    HAS_CHROMA = True
except ImportError:
    import logging

    logging.getLogger(__name__).warning(
        "ChromaDB not found. Please install with: pip install llama-index-vector-stores-chroma chromadb"
    )
    HAS_CHROMA = False

try:
    from .indexer import create_code_index
    from .retriever import CodeRetriever

    __all__ = ["create_code_index", "CodeRetriever", "HAS_CHROMA"]
except ImportError as e:
    import logging

    logging.getLogger(__name__).warning(f"Could not import all ragcode components: {e}")
    __all__ = ["HAS_CHROMA"]
