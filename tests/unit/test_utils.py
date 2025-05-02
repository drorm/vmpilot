"""
Unit tests for the utils module.

Tests the utility functions provided in the utils module.
"""

import json
import unittest
from unittest.mock import patch

from vmpilot.utils import extract_text_from_message_content, serialize_for_storage


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def test_extract_text_from_none(self):
        """Test extracting text from None."""
        result = extract_text_from_message_content(None)
        self.assertEqual(result, "")

    def test_extract_text_from_string(self):
        """Test extracting text from a simple string."""
        result = extract_text_from_message_content("Hello, world!")
        self.assertEqual(result, "Hello, world!")

    def test_extract_text_from_empty_string(self):
        """Test extracting text from an empty string."""
        result = extract_text_from_message_content("")
        self.assertEqual(result, "")

    def test_extract_text_from_list_with_strings(self):
        """Test extracting text from a list of strings."""
        content = ["Hello", "world"]
        result = extract_text_from_message_content(content)
        self.assertEqual(result, "Hello world")

    def test_extract_text_from_list_with_text_blocks(self):
        """Test extracting text from a list of text blocks (Anthropic/OpenAI format)."""
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "world"},
        ]
        result = extract_text_from_message_content(content)
        self.assertEqual(result, "Hello world")

    def test_extract_text_from_mixed_list(self):
        """Test extracting text from a list with mixed content types."""
        content = [
            {"type": "text", "text": "Hello"},
            "world",
            {"type": "image", "image_url": "http://example.com/image.jpg"},
        ]
        result = extract_text_from_message_content(content)
        self.assertEqual(result, "Hello world")

    def test_extract_text_from_dict_with_text(self):
        """Test extracting text from a dictionary with a text field."""
        content = {"text": "Hello, world!"}
        result = extract_text_from_message_content(content)
        self.assertEqual(result, "Hello, world!")

    def test_extract_text_from_other_dict(self):
        """Test extracting text from a dictionary without a text field."""
        content = {"foo": "bar", "baz": 123}
        result = extract_text_from_message_content(content)
        self.assertEqual(result, json.dumps(content))

    def test_extract_text_json_error(self):
        """Test extracting text when JSON serialization fails."""

        # Create an object that can't be serialized to JSON
        class UnserializableObject:
            def __repr__(self):
                return "UnserializableObject()"

        content = {"circular_ref": UnserializableObject()}

        # Patch json.dumps to raise an exception
        with patch("json.dumps", side_effect=TypeError("Cannot serialize")):
            result = extract_text_from_message_content(content)
            self.assertEqual(result, str(content))

    def test_serialize_for_storage_none(self):
        """Test serializing None for storage."""
        result = serialize_for_storage(None)
        self.assertEqual(result, "")

    def test_serialize_for_storage_string(self):
        """Test serializing a string for storage."""
        result = serialize_for_storage("Hello, world!")
        self.assertEqual(result, "Hello, world!")

    def test_serialize_for_storage_dict(self):
        """Test serializing a dictionary for storage."""
        data = {"foo": "bar", "baz": 123}
        result = serialize_for_storage(data)
        self.assertEqual(result, json.dumps(data))

    def test_serialize_for_storage_list(self):
        """Test serializing a list for storage."""
        data = ["foo", "bar", 123]
        result = serialize_for_storage(data)
        self.assertEqual(result, json.dumps(data))

    def test_serialize_for_storage_json_error(self):
        """Test serializing when JSON serialization fails."""

        # Create an object that can't be serialized to JSON
        class UnserializableObject:
            def __repr__(self):
                return "UnserializableObject()"

        data = {"circular_ref": UnserializableObject()}

        # Patch json.dumps to raise an exception
        with patch("json.dumps", side_effect=TypeError("Cannot serialize")):
            result = serialize_for_storage(data)
            self.assertEqual(result, str(data))


if __name__ == "__main__":
    unittest.main()
