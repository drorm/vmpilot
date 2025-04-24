"""
Utility functions for VMPilot.
"""

import json
from typing import Any, Dict, List, Optional, Union


def extract_text_from_message_content(content: Any) -> str:
    """
    Extract text content from various message content formats.

    Handles different API formats:
    - Simple string content
    - List of content blocks (Anthropic/OpenAI)
    - Dictionary with text field

    Args:
        content: Message content in various possible formats

    Returns:
        Extracted text as a string
    """
    # If content is None, return empty string
    if content is None:
        return ""

    # If content is already a string, return it
    if isinstance(content, str):
        return content

    # If content is a list (like Anthropic/OpenAI format)
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                # Handle text blocks
                if item.get("type") == "text" and "text" in item:
                    text_parts.append(item["text"])
                # Handle other block types as needed
            elif isinstance(item, str):
                text_parts.append(item)
        return " ".join(text_parts)

    # If content is a dict with a text field
    if isinstance(content, dict) and "text" in content:
        return content["text"]

    # If we can't extract text in a known format, convert to JSON string
    try:
        return json.dumps(content)
    except:
        return str(content)


def serialize_for_storage(data: Any) -> str:
    """
    Serialize complex data structures for storage in SQLite.

    Args:
        data: Any Python data structure

    Returns:
        JSON string representation
    """
    if data is None:
        return None

    if isinstance(data, str):
        return data

    try:
        return json.dumps(data)
    except:
        return str(data)
