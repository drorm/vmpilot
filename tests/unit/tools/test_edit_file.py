import os
import pytest
from pathlib import Path
from vmpilot.tools.edit_tool import EditTool


class TestEditTool:
    @pytest.fixture
    def edit_tool(self):
        return EditTool()

    @pytest.fixture
    def sample_file(self, tmp_path):
        """Create a sample file for testing."""
        file_path = tmp_path / "test.txt"
        content = "Hello, World!\nThis is a test file.\nMultiple lines here.\n"
        file_path.write_text(content)
        return file_path

    def test_basic_text_replacement(self, edit_tool, sample_file):
        """Test basic text replacement functionality."""
        edit_content = f"{sample_file}\n<<<<<<< SEARCH\nHello, World!\n=======\nGoodbye, World!\n>>>>>>> REPLACE"
        result = edit_tool.run(edit_content)
        assert "Successfully edited" in result
        assert (
            sample_file.read_text()
            == "Goodbye, World!\nThis is a test file.\nMultiple lines here.\n"
        )

    def test_multiple_replacements(self, edit_tool, sample_file):
        """Test multiple replacements in the same file."""
        edit_content = (
            f"{sample_file}\n"
            + "<<<<<<< SEARCH\nHello, World!\n=======\nGoodbye, World!\n>>>>>>> REPLACE\n"
            + f"{sample_file}\n"
            + "<<<<<<< SEARCH\nThis is a test file.\n=======\nThis is an edited file.\n>>>>>>> REPLACE"
        )
        result = edit_tool.run(edit_content)
        expected = "Goodbye, World!\nThis is an edited file.\nMultiple lines here.\n"
        assert sample_file.read_text() == expected

    def test_file_not_found(self, edit_tool, tmp_path):
        """Test behavior when file doesn't exist."""
        non_existent = tmp_path / "nonexistent.txt"
        edit_content = f"{non_existent}\n<<<<<<< SEARCH\nsome text\n=======\nnew text\n>>>>>>> REPLACE"
        with pytest.raises(FileNotFoundError):
            edit_tool.run(edit_content)

    def test_invalid_diff_format(self, edit_tool, sample_file):
        """Test handling of invalid diff format."""
        invalid_content = f"{sample_file}\nThis is not a valid diff format"
        with pytest.raises(ValueError):
            edit_tool.run(invalid_content)

    def test_no_matches(self, edit_tool, sample_file):
        """Test behavior when search text doesn't match."""
        edit_content = f"{sample_file}\n<<<<<<< SEARCH\nNon-existent text\n=======\nNew text\n>>>>>>> REPLACE"
        result = edit_tool.run(edit_content)
        assert "No matches found" in result
        # File should remain unchanged
        original_content = "Hello, World!\nThis is a test file.\nMultiple lines here.\n"
        assert sample_file.read_text() == original_content

    def test_multiple_files(self, edit_tool, tmp_path):
        """Test editing multiple files at once"""
        # Create two test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("Hello World\nThis is file 1\n")
        file2.write_text("Hello World\nThis is file 2\n")

        # Create content with edits for both files
        content = f"{file1}\n"
        content += "<<<<<<< SEARCH\nHello World\n=======\nGoodbye World\n>>>>>>> REPLACE\n\n"
        content += f"{file2}\n"
        content += "<<<<<<< SEARCH\nThis is file 2\n=======\nThis is the second file\n>>>>>>> REPLACE"

        result = edit_tool.run(content)
        assert "Successfully edited" in result

        # Verify both files were edited correctly
        assert file1.read_text() == "Goodbye World\nThis is file 1\n"
        assert file2.read_text() == "Hello World\nThis is the second file\n"

    def test_multiple_files_one_missing(self, edit_tool, tmp_path):
        """Test editing multiple files where one doesn't exist"""
        # Create only the first file
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "nonexistent.txt"  # This file won't exist
        
        file1.write_text("Hello World\nThis is file 1\n")

        # Create content with edits for both files
        content = f"{file1}\n"
        content += "<<<<<<< SEARCH\nHello World\n=======\nGoodbye World\n>>>>>>> REPLACE\n\n"
        content += f"{file2}\n"
        content += "<<<<<<< SEARCH\nThis is file 2\n=======\nThis is the second file\n>>>>>>> REPLACE"

        with pytest.raises(FileNotFoundError) as excinfo:
            edit_tool.run(content)
        assert str(file2) in str(excinfo.value)
