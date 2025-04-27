"""
Integration tests for the code retrieval system.
Tests the integration between the CodeRetrievalTool and the CodeRetriever.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vmpilot.tools.code_retrieval_tool import CodeRetrievalTool


@pytest.fixture
def mock_retriever():
    """Create a mock CodeRetriever."""
    mock = MagicMock()
    mock.retrieve.return_value = [
        {
            "content": "class Calculator:\n    def add(self, a, b):\n        return a + b",
            "metadata": {"file_path": "calculator.py", "language": "python"},
            "score": 0.95,
            "structure_info": {
                "type": "Class",
                "name": "Calculator",
                "description": "A simple calculator class",
            },
        }
    ]
    return mock


@pytest.fixture
def vector_store_dir():
    """Create a temporary directory for the vector store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_code_retrieval_tool_integration(vector_store_dir, mock_retriever):
    """Test the integration between CodeRetrievalTool and CodeRetriever."""
    # Create a test vector store directory
    Path(vector_store_dir).mkdir(parents=True, exist_ok=True)

    # Initialize the tool with the mock retriever
    with patch(
        "vmpilot.tools.code_retrieval_tool.CodeRetriever", return_value=mock_retriever
    ):
        tool = CodeRetrievalTool(vector_store_dir=vector_store_dir)

        # Verify the tool is initialized
        assert tool.is_initialized
        assert tool.retriever == mock_retriever

        # Test running the tool
        result = tool._run("calculator class")

        # Verify the retriever was called correctly
        mock_retriever.retrieve.assert_called_once_with("calculator class", {})

        # Verify the result contains the expected information
        assert "Calculator" in result
        assert "calculator.py" in result
        assert "Score: 0.95" in result
        assert "A simple calculator class" in result


def test_code_retrieval_with_filters(vector_store_dir, mock_retriever):
    """Test code retrieval with file path and language filters."""
    # Initialize the tool with the mock retriever
    with patch(
        "vmpilot.tools.code_retrieval_tool.CodeRetriever", return_value=mock_retriever
    ):
        tool = CodeRetrievalTool(vector_store_dir=vector_store_dir)

        # Test running the tool with filters
        result = tool._run(
            query="calculator class",
            file_path="src/calculator.py",
            language="python",
        )

        # Verify the retriever was called with the correct context
        mock_retriever.retrieve.assert_called_once_with(
            "calculator class",
            {"file_path": "src/calculator.py", "language": "python"},
        )


def test_code_retrieval_async(vector_store_dir, mock_retriever):
    """Test the async version of the code retrieval tool."""
    # Initialize the tool with the mock retriever
    with patch(
        "vmpilot.tools.code_retrieval_tool.CodeRetriever", return_value=mock_retriever
    ):
        tool = CodeRetrievalTool(vector_store_dir=vector_store_dir)

        # Test running the tool asynchronously
        import asyncio

        result = asyncio.run(tool._arun("calculator class"))

        # Verify the retriever was called correctly
        mock_retriever.retrieve.assert_called_once_with("calculator class", {})

        # Verify the result contains the expected information
        assert "Calculator" in result


def test_code_retrieval_error_handling(vector_store_dir, mock_retriever):
    """Test error handling in the code retrieval tool."""
    # Make the retriever raise an exception
    mock_retriever.retrieve.side_effect = Exception("Test error")

    # Initialize the tool with the mock retriever
    with patch(
        "vmpilot.tools.code_retrieval_tool.CodeRetriever", return_value=mock_retriever
    ):
        tool = CodeRetrievalTool(vector_store_dir=vector_store_dir)

        # Test running the tool with an error
        result = tool._run("calculator class")

        # Verify the error message is in the result
        assert "Error retrieving code" in result
        assert "Test error" in result
