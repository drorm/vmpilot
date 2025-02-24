import os
from pathlib import Path

import pytest

from vmpilot.tools.edit_tool import EditTool


class TestEditToolExtended:
    @pytest.fixture
    def edit_tool(self):
        return EditTool()

    @pytest.fixture
    def empty_file(self, tmp_path):
        """Create an empty file for testing."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")
        return file_path

    def test_empty_file(self, edit_tool, empty_file):
        """Test handling of empty files."""
        edit_content = f"{empty_file}\n<<<<<<< SEARCH\n\n=======\nNew content\n>>>>>>> REPLACE"
        result = edit_tool.run(edit_content)
        assert "" in result
        assert empty_file.read_text() == "New content\n"

    def test_whitespace_handling(self, edit_tool, tmp_path):
        """Test handling of whitespace in patterns."""
        file_path = tmp_path / "whitespace.txt"
        file_path.write_text("  Leading space\nTrailing space  \n  Both  \n")
        
        edit_content = f"{file_path}\n<<<<<<< SEARCH\n  Leading space\n=======\nNo leading space\n>>>>>>> REPLACE"
        edit_tool.run(edit_content)
        
        # Verify exact whitespace matching
        assert file_path.read_text() == "No leading space\nTrailing space  \n  Both  \n"

    def test_multiline_pattern(self, edit_tool, tmp_path):
        """Test matching patterns that span multiple lines."""
        file_path = tmp_path / "multiline.txt"
        file_path.write_text("Line 1\nLine 2\nLine 3\nLine 4\n")
        
        edit_content = f"{file_path}\n<<<<<<< SEARCH\nLine 2\nLine 3\n=======\nReplaced\nContent\n>>>>>>> REPLACE"
        edit_tool.run(edit_content)
        
        assert file_path.read_text() == "Line 1\nReplaced\nContent\nLine 4\n"

    def test_special_characters(self, edit_tool, tmp_path):
        """Test handling of special characters."""
        file_path = tmp_path / "special.txt"
        content = "Tab\there\nNewline\nUnicode: 🌟\n"
        file_path.write_text(content)
        
        edit_content = f"{file_path}\n<<<<<<< SEARCH\nTab\there\n=======\nReplaced tab\n>>>>>>> REPLACE"
        edit_tool.run(edit_content)
        
        assert file_path.read_text() == "Replaced tab\nNewline\nUnicode: 🌟\n"

    def test_file_boundaries(self, edit_tool, tmp_path):
        """Test patterns at file start and end."""
        file_path = tmp_path / "boundaries.txt"
        content = "First line\nMiddle\nLast line\n"
        file_path.write_text(content)
        
        # Replace at start
        edit_content = f"{file_path}\n<<<<<<< SEARCH\nFirst line\n=======\nNew first line\n>>>>>>> REPLACE"
        edit_tool.run(edit_content)
        
        # Replace at end
        edit_content = f"{file_path}\n<<<<<<< SEARCH\nLast line\n=======\nNew last line\n>>>>>>> REPLACE"
        edit_tool.run(edit_content)
        
        assert file_path.read_text() == "New first line\nMiddle\nNew last line\n"

    def test_large_file(self, edit_tool, tmp_path):
        """Test handling of large files."""
        file_path = tmp_path / "large.txt"
        # Create a 1MB file
        content = "This is a test line\n" * 50000
        file_path.write_text(content)
        
        edit_content = f"{file_path}\n<<<<<<< SEARCH\nThis is a test line\n=======\nReplaced line\n>>>>>>> REPLACE"
        result = edit_tool.run(edit_content)
        
        # Check first line was replaced
        assert file_path.read_text().startswith("Replaced line\n")

    def test_binary_file(self, edit_tool, tmp_path):
        """Test that binary files are handled appropriately."""
        file_path = tmp_path / "binary.bin"
        # Create a simple binary file
        with open(file_path, 'wb') as f:
            f.write(bytes(range(256)))
        
        edit_content = f"{file_path}\n<<<<<<< SEARCH\nsome text\n=======\nnew text\n>>>>>>> REPLACE"
        with pytest.raises(UnicodeDecodeError):
            edit_tool.run(edit_content)

    def test_readonly_file(self, edit_tool, tmp_path):
        """Test handling of read-only files."""
        file_path = tmp_path / "readonly.txt"
        file_path.write_text("This is a read-only file\n")
        # Make file read-only
        os.chmod(file_path, 0o444)
        
        edit_content = f"{file_path}\n<<<<<<< SEARCH\nThis is a read-only file\n=======\nTrying to modify\n>>>>>>> REPLACE"
        with pytest.raises(PermissionError):
            edit_tool.run(edit_content)