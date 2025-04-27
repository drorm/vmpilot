"""
Unit tests for the code retrieval system.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragcode.indexer import create_code_index
from ragcode.retriever import CodeRetriever
from vmpilot.tools.code_retrieval_tool import CodeRetrievalTool


@pytest.fixture
def sample_code_dir():
    """Create a temporary directory with sample code files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a Python file
        with open(os.path.join(tmpdir, "sample.py"), "w") as f:
            f.write(
                """
def hello_world():
    \"\"\"Print hello world message.\"\"\"
    print("Hello, World!")

class Calculator:
    \"\"\"A simple calculator class.\"\"\"
    
    def add(self, a, b):
        \"\"\"Add two numbers.\"\"\"
        return a + b
    
    def subtract(self, a, b):
        \"\"\"Subtract b from a.\"\"\"
        return a - b
"""
            )

        # Create a markdown file
        with open(os.path.join(tmpdir, "README.md"), "w") as f:
            f.write(
                """
# Sample Project

This is a sample project for testing the code retrieval system.

## Features

- Simple calculator
- Hello world function
"""
            )

        yield tmpdir


@pytest.fixture
def vector_store_dir():
    """Create a temporary directory for the vector store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.mark.skip(reason="Requires OpenAI API key")
def test_create_code_index(sample_code_dir, vector_store_dir):
    """Test creating a code index from sample files."""
    # Create the index
    index = create_code_index(
        source_dir=sample_code_dir,
        vector_store_dir=vector_store_dir,
        file_extensions=[".py", ".md"],
        languages=["python"],
    )

    # Verify the index was created
    assert index is not None
    assert Path(vector_store_dir).exists()


@pytest.mark.skip(reason="Requires OpenAI API key")
def test_code_retriever(sample_code_dir, vector_store_dir):
    """Test retrieving code with the CodeRetriever."""
    # Create the index
    create_code_index(
        source_dir=sample_code_dir,
        vector_store_dir=vector_store_dir,
        file_extensions=[".py", ".md"],
        languages=["python"],
    )

    # Create the retriever
    retriever = CodeRetriever(
        vector_store_dir=vector_store_dir,
        similarity_top_k=3,
    )

    # Test retrieval
    results = retriever.retrieve("calculator class")
    assert len(results) > 0
    assert any("Calculator" in result["content"] for result in results)


def test_code_retrieval_tool_not_initialized():
    """Test CodeRetrievalTool when index is not initialized."""
    # Create the tool with a non-existent vector store directory
    tool = CodeRetrievalTool(vector_store_dir="/non/existent/path")

    # Verify the tool is not initialized
    assert not tool.is_initialized

    # Test running the tool
    result = tool._run("calculator class")
    assert "Code index not found" in result


@pytest.mark.skip(reason="Requires OpenAI API key")
def test_code_retrieval_tool(sample_code_dir, vector_store_dir):
    """Test CodeRetrievalTool with a sample index."""
    # Create the index
    create_code_index(
        source_dir=sample_code_dir,
        vector_store_dir=vector_store_dir,
        file_extensions=[".py", ".md"],
        languages=["python"],
    )

    # Create the tool
    tool = CodeRetrievalTool(vector_store_dir=vector_store_dir)

    # Verify the tool is initialized
    assert tool.is_initialized

    # Test running the tool
    result = tool._run("calculator class")
    assert "Calculator" in result
    assert "sample.py" in result
