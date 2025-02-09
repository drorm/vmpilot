import os
from pathlib import Path

import pytest

from vmpilot.tools.create_file import CreateFileTool


class TestCreateFileTool:
    @pytest.fixture
    def create_file_tool(self):
        return CreateFileTool()

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Provides a temporary file path that gets cleaned up after the test"""
        return tmp_path / "test_file.txt"

    def test_create_new_file(self, create_file_tool, temp_file):
        """Test creating a new file with content"""
        content = "Hello, World!"
        result = create_file_tool.run({"path": str(temp_file), "content": content})

        assert temp_file.exists()
        assert temp_file.read_text() == content
        assert "File created" in result

    def test_create_file_with_nested_path(self, create_file_tool, tmp_path):
        """Test creating a file in nested directories"""
        nested_path = tmp_path / "nested" / "path" / "test_file.txt"
        content = "Test content"

        result = create_file_tool.run({"path": str(nested_path), "content": content})

        assert nested_path.exists()
        assert nested_path.read_text() == content

    def test_create_file_already_exists(self, create_file_tool, temp_file):
        """Test attempting to create a file that already exists"""
        # Create file first
        temp_file.write_text("Original content")

        with pytest.raises(FileExistsError):
            create_file_tool.run({"path": str(temp_file), "content": "New content"})

        # Verify original content wasn't changed
        assert temp_file.read_text() == "Original content"

    def test_create_file_invalid_path(self, create_file_tool):
        """Test creating a file with invalid path"""
        with pytest.raises(ValueError):
            create_file_tool.run({"path": "", "content": "test"})

    def test_create_file_with_unicode(self, create_file_tool, temp_file):
        """Test creating a file with unicode content"""
        content = "Hello, 世界! 🌍"
        result = create_file_tool.run({"path": str(temp_file), "content": content})

        assert temp_file.exists()
        assert temp_file.read_text() == content
