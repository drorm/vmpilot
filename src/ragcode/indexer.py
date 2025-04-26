"""
Code indexing module for the RAG-based code retrieval system.
Uses Tree-sitter for structure-aware code chunking and vector embeddings for semantic search.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional

import chromadb
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import CodeSplitter
from llama_index.core.schema import Document
from llama_index.embeddings.openai import OpenAIEmbedding

# Using Chroma vector store
from llama_index.vector_stores.chroma import ChromaVectorStore

# Import our enhanced code splitter
from ragcode.enhanced_code_splitter import EnhancedCodeSplitter

logger = logging.getLogger(__name__)


def create_code_index(
    source_dir: str,
    vector_store_dir: str,
    embedding_model: str = "text-embedding-3-small",
    file_extensions: List[str] = [".py", ".md", ".txt", ".json", ".yaml", ".yml"],
    languages: List[str] = ["python"],
    chunk_lines: int = 200,
    chunk_lines_overlap: int = 125,
) -> VectorStoreIndex:
    """
    Create a code index from source files.

    Args:
        source_dir: Directory containing source code
        vector_store_dir: Directory to persist the vector store
        embedding_model: Name of the embedding model to use
        file_extensions: List of file extensions to index
        languages: List of programming languages to support
        chunk_lines: Number of lines per chunk
        chunk_lines_overlap: Overlap between consecutive chunks

    Returns:
        VectorStoreIndex: The created index
    """
    logger.info(f"Loading documents from {source_dir}")

    # Ensure the source directory exists
    source_path = Path(source_dir)
    if not source_path.exists():
        raise ValueError(f"Source directory {source_dir} does not exist")

    # Create vector store directory if it doesn't exist
    vector_store_path = Path(vector_store_dir)
    vector_store_path.mkdir(parents=True, exist_ok=True)

    # Configure embedding model
    embedding_model_obj = OpenAIEmbedding(model=embedding_model)
    Settings.embed_model = embedding_model_obj
    documents = SimpleDirectoryReader(
        input_dir=source_dir,
        required_exts=file_extensions,
        recursive=True,
    ).load_data()

    logger.info(f"Loaded {len(documents)} documents")

    # Configure the embedding model
    embedding_model = OpenAIEmbedding(model=embedding_model)
    Settings.embed_model = embedding_model

    # Create code splitter for each supported language
    all_nodes = []
    for language in languages:
        logger.info(f"Splitting code for language: {language}")
        code_splitter = EnhancedCodeSplitter(
            language=language,
            chunk_lines=chunk_lines,
            chunk_lines_overlap=chunk_lines_overlap,
        )

        # Filter documents by language
        language_docs = filter_documents_by_language(documents, language)
        if language_docs:
            nodes = code_splitter.get_nodes_from_documents(language_docs)
            all_nodes.extend(nodes)
            logger.info(f"Created {len(nodes)} nodes for {language}")

    # Create Chroma client and collection
    logger.info("Creating Chroma vector store index")
    chroma_client = chromadb.PersistentClient(path=str(vector_store_path))
    chroma_collection = chroma_client.get_or_create_collection("code_chunks")

    # Manually embed and add nodes into Chroma
    logger.info("Generating embeddings and inserting into Chroma")
    ids = [node.id_ for node in all_nodes]
    documents = [node.get_content() for node in all_nodes]
    metadatas = [node.metadata for node in all_nodes]
    embeddings = embedding_model_obj.get_text_embedding_batch(documents)

    chroma_collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    # Now create a ChromaVectorStore and wrap it
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # Build VectorStoreIndex wrapping around already inserted Chroma
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # Save the index
    index.storage_context.persist(persist_dir=str(vector_store_path))

    logger.info(f"Indexing complete with {len(all_nodes)} total nodes")
    return index


def filter_documents_by_language(
    documents: List[Document], language: str
) -> List[Document]:
    """
    Filter documents by file extension to match the specified language.

    Args:
        documents: List of documents to filter
        language: Programming language to filter by

    Returns:
        List[Document]: Filtered documents
    """
    extension_map = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".ts", ".tsx"],
        "java": [".java"],
        "go": [".go"],
        "rust": [".rs"],
        "c": [".c", ".h"],
        "cpp": [".cpp", ".hpp", ".cc", ".hh"],
    }

    extensions = extension_map.get(language.lower(), [])
    if not extensions:
        logger.warning(f"No file extensions defined for language {language}")
        return []

    filtered_docs = []
    for doc in documents:
        file_path = doc.metadata.get("file_path", "")
        if any(file_path.endswith(ext) for ext in extensions):
            filtered_docs.append(doc)

    return filtered_docs


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: python indexer.py <source_dir> <vector_store_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    vector_store_dir = sys.argv[2]

    logging.basicConfig(level=logging.INFO)
    create_code_index(source_dir, vector_store_dir)
