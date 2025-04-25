"""
RAG-based code retrieval system for VMPilot.
Provides structure-aware code indexing and hybrid retrieval capabilities.

Dependencies:
- llama-index>=0.10.7
- llama-index-core>=0.10.7
- llama-index-embeddings-openai>=0.1.5
- llama-index-vector-stores-chroma>=0.1.1 (optional, falls back to SimpleVectorStore)
- chromadb>=0.4.18 (required for ChromaVectorStore)
- tree-sitter>=0.20.1
"""

try:
    from .indexer import create_code_index
    from .retriever import CodeRetriever

    __all__ = ["create_code_index", "CodeRetriever"]
except ImportError as e:
    import logging

    logging.getLogger(__name__).warning(f"Could not import all ragcode components: {e}")
    __all__ = []
