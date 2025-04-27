"""
Enhanced code splitter that adds richer metadata to code chunks.
"""

import logging
import re
from typing import Dict, List, Optional

from llama_index.core.node_parser import CodeSplitter
from llama_index.core.schema import (
    Document,
    NodeRelationship,
    RelatedNodeInfo,
    TextNode,
)

logger = logging.getLogger(__name__)


class EnhancedCodeSplitter(CodeSplitter):
    """
    Enhanced code splitter that adds richer metadata to code chunks.

    This extends the standard CodeSplitter to:
    1. Add detailed code structure information
    2. Include function/class names and types in the metadata
    3. Add parent-child relationships
    """

    def get_nodes_from_documents(self, documents: List[Document]) -> List[TextNode]:
        """
        Process documents into nodes with enhanced metadata.

        Args:
            documents: List of documents to process

        Returns:
            List of TextNode objects with enhanced metadata
        """
        # First, use the standard CodeSplitter to get the base nodes
        nodes = super().get_nodes_from_documents(documents)

        # Now enhance the nodes with additional metadata
        enhanced_nodes = []

        for node in nodes:
            # Get the node content
            content = node.text

            # Extract existing metadata
            metadata = dict(node.metadata)

            # Add code structure metadata
            structure_info = self._extract_code_structure(content)
            metadata.update(structure_info)

            # Create a new node with enhanced metadata
            enhanced_node = TextNode(
                text=content,
                metadata=metadata,
                relationships=node.relationships,
                id_=node.id_,
            )
            enhanced_nodes.append(enhanced_node)

        return enhanced_nodes

    def _extract_code_structure(self, content: str) -> Dict[str, str]:
        """
        Extract code structure information from content.

        Args:
            content: The code content

        Returns:
            Dictionary of structure metadata
        """
        structure_info = {}

        # Detect if this is a class definition (check this first as it's more specific)
        class_match = re.search(r"class\s+(\w+)(?:\(([^)]*)\))?:", content)
        if class_match:
            structure_info["code_type"] = "class"
            structure_info["class_name"] = class_match.group(1)
            if class_match.group(2):
                structure_info["parent_classes"] = class_match.group(2)

        # Detect if this is a function definition (only set if not already a class)
        func_match = re.search(r"def\s+(\w+)\s*\(", content)
        if func_match:
            # Only set code_type to function if we haven't identified this as a class
            if "code_type" not in structure_info:
                structure_info["code_type"] = "function"

            # Always record the function name if found (classes can contain methods)
            structure_info["function_name"] = func_match.group(1)

            # Check if it's a method (indented and/or has self parameter)
            if "self" in content or content.startswith("    def "):
                structure_info["is_method"] = "true"

        # Add language-specific tags
        if "file_path" in structure_info:
            file_path = structure_info["file_path"]
            if file_path.endswith(".py"):
                structure_info["language"] = "python"
            elif file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
                structure_info["language"] = "javascript"
            elif file_path.endswith(".java"):
                structure_info["language"] = "java"
            elif file_path.endswith(".go"):
                structure_info["language"] = "go"
            elif file_path.endswith(".rb"):
                structure_info["language"] = "ruby"

        # Extract import statements
        imports = re.findall(r"(?:import|from)\s+([^\s;]+)", content)
        if imports:
            structure_info["imports"] = ", ".join(imports)

        # Detect docstrings
        docstring_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if docstring_match:
            structure_info["has_docstring"] = "true"
            # Extract a short description from the docstring
            docstring = docstring_match.group(1).strip()
            first_line = docstring.split("\n")[0].strip()
            structure_info["description"] = first_line[:100]  # Limit to 100 chars

        return structure_info
