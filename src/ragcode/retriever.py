"""
Code retrieval module for the RAG-based code retrieval system.
Provides hybrid retrieval combining vector search with re-ranking.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import chromadb
from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.language_models import LLM
from langchain_core.retrievers import BaseRetriever
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever as LlamaIndexRetriever
from llama_index.embeddings.openai import OpenAIEmbedding

# Using Chroma vector store
from llama_index.vector_stores.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)


class CodeRetriever:
    """
    Hybrid retriever for code understanding, combining vector search with re-ranking.
    Provides a LangChain-compatible interface with fallback to shell commands.
    """

    def __init__(
        self,
        vector_store_dir: str,
        embedding_model: str = "text-embedding-3-small",
        similarity_top_k: int = 5,
        rerank_top_n: int = 3,
        llm: Optional[LLM] = None,
    ):
        """
        Initialize the code retriever.

        Args:
            vector_store_dir: Directory containing the vector store
            embedding_model: Name of the embedding model to use
            similarity_top_k: Number of similar documents to retrieve
            rerank_top_n: Number of documents to keep after re-ranking
            llm: Language model for re-ranking (optional)
        """
        self.vector_store_dir = vector_store_dir
        self.embedding_model = embedding_model
        self.similarity_top_k = similarity_top_k
        self.rerank_top_n = rerank_top_n
        self.llm = llm

        # Load the vector store if it exists
        vector_store_path = Path(vector_store_dir)
        if vector_store_path.exists():
            logger.info(f"Loading vector store from {vector_store_dir}")
            # Temporary solution using loading from storage context instead of ChromaVectorStore
            self.embed_model = OpenAIEmbedding(model=embedding_model)
            try:
                # Try to load using Chroma
                chroma_client = chromadb.PersistentClient(path=str(vector_store_path))
                chroma_collection = chroma_client.get_or_create_collection(
                    "code_chunks"
                )
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    embed_model=self.embed_model,
                )
            except Exception as e:
                logger.error(f"Error loading index: {str(e)}")
                # Fallback to empty Chroma index
                try:
                    chroma_client = chromadb.PersistentClient(
                        path=str(vector_store_path)
                    )
                    chroma_collection = chroma_client.get_or_create_collection(
                        "code_chunks"
                    )
                    vector_store = ChromaVectorStore(
                        chroma_collection=chroma_collection
                    )
                    self.index = VectorStoreIndex.from_vector_store(
                        vector_store=vector_store,
                        embed_model=self.embed_model,
                    )
                except Exception as e2:
                    logger.error(f"Error creating fallback index: {str(e2)}")
                    # Last resort fallback
                    from llama_index.core.vector_stores import SimpleVectorStore

                    self.vector_store = SimpleVectorStore()
                    self.index = VectorStoreIndex.from_vector_store(
                        vector_store=self.vector_store,
                        embed_model=self.embed_model,
                    )
            self.retriever = self.index.as_retriever(similarity_top_k=similarity_top_k)
            self.is_initialized = True
        else:
            logger.warning(f"Vector store directory {vector_store_dir} does not exist")
            self.is_initialized = False

    def retrieve(
        self, query: str, context: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """
        Retrieve code chunks relevant to the query.

        Args:
            query: Query string
            context: Additional context for the query (e.g., file path, language)

        Returns:
            List of dictionaries with code chunks and metadata
        """
        if not self.is_initialized:
            logger.warning("Vector store not initialized, returning empty results")
            return []

        # Enhance query with context if provided
        enhanced_query = query
        if context:
            file_path = context.get("file_path", "")
            language = context.get("language", "")
            if file_path or language:
                context_parts = []
                if file_path:
                    context_parts.append(f"in file {file_path}")
                if language:
                    context_parts.append(f"in {language} language")
                enhanced_query = f"{query} ({', '.join(context_parts)})"

        # Retrieve similar nodes
        logger.info(f"Retrieving documents for query: {enhanced_query}")
        nodes = self.retriever.retrieve(enhanced_query)

        # Re-rank if LLM is provided
        if self.llm and len(nodes) > self.rerank_top_n:
            logger.info(f"Re-ranking {len(nodes)} nodes to top {self.rerank_top_n}")
            nodes = self._rerank_nodes(query, nodes, self.rerank_top_n)

        # Deduplicate results
        deduplicated_nodes = self._deduplicate_nodes(nodes)

        # Convert to dictionaries with enhanced information
        results = []
        for node in deduplicated_nodes:
            # Get code structure information from metadata
            metadata = node.metadata
            structure_info = self._extract_structure_info(metadata)

            # Prepare the result with enhanced information
            results.append(
                {
                    "content": node.text,
                    "metadata": metadata,
                    "score": node.score if hasattr(node, "score") else 0.0,
                    "structure_info": structure_info,
                }
            )

        return results

    def _deduplicate_nodes(self, nodes):
        """
        Remove duplicate nodes based on content.

        Args:
            nodes: List of nodes to deduplicate

        Returns:
            List of deduplicated nodes
        """
        seen_content = set()
        deduplicated = []

        for node in nodes:
            # Use a hash of the content as a deduplication key
            content_hash = hash(node.text)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                deduplicated.append(node)

        return deduplicated

    def _extract_structure_info(self, metadata):
        """
        Extract and format code structure information from metadata.

        Args:
            metadata: Node metadata

        Returns:
            Formatted structure information
        """
        structure_info = {}

        # Extract code type and name
        code_type = metadata.get("code_type", "")
        if code_type == "class":
            structure_info["type"] = "Class"
            structure_info["name"] = metadata.get("class_name", "")
            structure_info["parent_classes"] = metadata.get("parent_classes", "")
        elif code_type == "function":
            if metadata.get("is_method") == "true":
                structure_info["type"] = "Method"
            else:
                structure_info["type"] = "Function"
            structure_info["name"] = metadata.get("function_name", "")

        # Add description if available
        if "description" in metadata:
            structure_info["description"] = metadata["description"]

        return structure_info

    def _rerank_nodes(self, query: str, nodes: List, top_n: int) -> List:
        """
        Re-rank nodes using the LLM to prioritize most relevant chunks.

        Args:
            query: Original query
            nodes: Retrieved nodes
            top_n: Number of nodes to keep

        Returns:
            Re-ranked list of nodes
        """
        if not self.llm:
            return nodes[:top_n]

        # TODO: Implement re-ranking logic with LLM
        # For now, just return the top N nodes by similarity score
        return sorted(
            nodes, key=lambda x: x.score if hasattr(x, "score") else 0.0, reverse=True
        )[:top_n]

    def to_langchain_retriever(self) -> BaseRetriever:
        """
        Convert to a LangChain-compatible retriever.

        Returns:
            LangChain BaseRetriever
        """
        return LangChainCodeRetriever(code_retriever=self)


class LangChainCodeRetriever(BaseRetriever):
    """
    LangChain-compatible wrapper for the CodeRetriever.
    """

    code_retriever: CodeRetriever

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun, **kwargs
    ) -> List[Document]:
        """
        Get documents relevant to the query.

        Args:
            query: Query string
            run_manager: Callback manager

        Returns:
            List of LangChain documents
        """
        context = kwargs.get("context", {})
        results = self.code_retriever.retrieve(query, context)

        # Convert to LangChain documents
        documents = []
        for result in results:
            documents.append(
                Document(
                    page_content=result["content"],
                    metadata=result["metadata"],
                )
            )

        return documents
