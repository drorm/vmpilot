"""
Unit tests for the EnhancedCodeSplitter class.
"""

from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.schema import Document, TextNode

from ragcode.enhanced_code_splitter import EnhancedCodeSplitter


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            text="""
class Calculator:
    \"\"\"A simple calculator class.\"\"\"
    
    def add(self, a, b):
        \"\"\"Add two numbers.\"\"\"
        return a + b
    
    def subtract(self, a, b):
        \"\"\"Subtract b from a.\"\"\"
        return a - b
""",
            metadata={"file_path": "calculator.py"},
        ),
        Document(
            text="""
def hello_world():
    \"\"\"Print hello world message.\"\"\"
    print("Hello, World!")

# Import statements
import os
from pathlib import Path
""",
            metadata={"file_path": "hello.py"},
        ),
    ]


class TestEnhancedCodeSplitter:
    """Tests for the EnhancedCodeSplitter class."""

    @patch("llama_index.core.node_parser.CodeSplitter.get_nodes_from_documents")
    def test_get_nodes_from_documents(self, mock_super_get_nodes, sample_documents):
        """Test that the splitter adds enhanced metadata to nodes."""
        # Create mock nodes returned by the parent class
        mock_nodes = [
            TextNode(
                text=sample_documents[0].text,
                metadata={"file_path": "calculator.py"},
            ),
            TextNode(
                text=sample_documents[1].text,
                metadata={"file_path": "hello.py"},
            ),
        ]
        mock_super_get_nodes.return_value = mock_nodes

        # Create the splitter and get enhanced nodes
        splitter = EnhancedCodeSplitter(language="python")
        enhanced_nodes = splitter.get_nodes_from_documents(sample_documents)

        # Verify that the parent method was called
        mock_super_get_nodes.assert_called_once_with(sample_documents)

        # Verify that we got the expected number of nodes
        assert len(enhanced_nodes) == 2

        # Check class metadata
        calculator_node = enhanced_nodes[0]
        assert calculator_node.metadata["code_type"] == "class"
        assert calculator_node.metadata["class_name"] == "Calculator"
        assert calculator_node.metadata["has_docstring"] == "true"
        assert "A simple calculator class" in calculator_node.metadata["description"]

        # Check function metadata
        hello_node = enhanced_nodes[1]
        assert hello_node.metadata["code_type"] == "function"
        assert hello_node.metadata["function_name"] == "hello_world"
        assert hello_node.metadata["has_docstring"] == "true"
        assert "Print hello world message" in hello_node.metadata["description"]
        assert "os" in hello_node.metadata["imports"]
        assert "pathlib" in hello_node.metadata["imports"]

    def test_extract_code_structure_class(self):
        """Test extracting structure from a class definition."""
        splitter = EnhancedCodeSplitter(language="python")
        content = """
class Person(BaseModel):
    \"\"\"Represents a person entity.\"\"\"
    name: str
    age: int
        """
        metadata = splitter._extract_code_structure(content)

        assert metadata["code_type"] == "class"
        assert metadata["class_name"] == "Person"
        assert metadata["parent_classes"] == "BaseModel"
        assert metadata["has_docstring"] == "true"
        assert "Represents a person entity" in metadata["description"]

    def test_extract_code_structure_function(self):
        """Test extracting structure from a function definition."""
        splitter = EnhancedCodeSplitter(language="python")
        content = """
def calculate_sum(numbers):
    \"\"\"
    Calculate the sum of a list of numbers.
    
    Args:
        numbers: A list of numbers to sum
        
    Returns:
        The sum of all numbers
    \"\"\"
    return sum(numbers)
        """
        metadata = splitter._extract_code_structure(content)

        assert metadata["code_type"] == "function"
        assert metadata["function_name"] == "calculate_sum"
        assert metadata["has_docstring"] == "true"
        assert "Calculate the sum of a list of numbers" in metadata["description"]

    def test_extract_code_structure_method(self):
        """Test extracting structure from a method definition."""
        splitter = EnhancedCodeSplitter(language="python")
        content = """    def process_data(self, data):
        \"\"\"Process the provided data.\"\"\"
        return data.upper()
        """
        metadata = splitter._extract_code_structure(content)

        assert metadata["code_type"] == "function"
        assert metadata["function_name"] == "process_data"
        assert metadata["is_method"] == "true"
        assert metadata["has_docstring"] == "true"
        assert "Process the provided data" in metadata["description"]
