import os
import tempfile
import time

import pytest

from vmpilot.tools.shelltool import ShellTool


class TestShellToolExtended:
    @pytest.fixture
    def shell_tool(self):
        return ShellTool()

    def test_large_output_handling(self, shell_tool):
        """Test handling of commands that produce large outputs."""
        # Generate a command that produces a large output (100KB)
        result = shell_tool.run(
            {
                "command": "yes 'testing large output' | head -n 5000",
                "language": "text",
            }
        )
        # Verify the output contains expected content and is properly formatted
        assert "testing large output" in result
        assert "```text" in result
        assert "```" in result

    def test_special_character_handling(self, shell_tool):
        """Test commands with special characters."""
        # Command with quotes, dollar signs, and backticks
        result = shell_tool.run(
            {
                "command": 'echo "Special $HOME characters \\`whoami\\`"',
                "language": "bash",
            }
        )
        assert "Special" in result
        assert "$HOME" in result
        assert "whoami" in result

    def test_environment_variable_handling(self, shell_tool):
        """Test handling of environment variables in commands."""
        # Set a test environment variable
        os.environ["TEST_VAR"] = "test_value"
        result = shell_tool.run(
            {
                "command": "echo $TEST_VAR",
                "language": "bash",
            }
        )
        assert "test_value" in result

    def test_command_execution_in_different_directory(self, shell_tool):
        """Test executing commands in different directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file in the temp directory
            test_file_path = os.path.join(temp_dir, "test_file.txt")
            with open(test_file_path, "w") as f:
                f.write("test content")

            # Execute command in the temp directory
            result = shell_tool.run(
                {
                    "command": f"cd {temp_dir} && cat test_file.txt",
                    "language": "bash",
                }
            )
            assert "test content" in result

    def test_different_output_formats(self, shell_tool):
        """Test different language parameters for syntax highlighting."""
        # Python output
        result = shell_tool.run(
            {
                "command": "echo 'print(\"Hello, World!\")'",
                "language": "python",
            }
        )
        assert "```python" in result

        # JSON output
        result = shell_tool.run(
            {
                "command": 'echo \'{"key": "value"}\'',
                "language": "json",
            }
        )
        assert "```json" in result

    def test_command_with_error_exit_code(self, shell_tool):
        """Test handling of commands that exit with non-zero status."""
        result = shell_tool.run(
            {
                "command": "exit 1",
                "language": "bash",
            }
        )
        # Should not raise an exception but return the error
        assert result is not None

    def test_executable_not_found(self, shell_tool):
        """Test handling of non-existent commands."""
        result = shell_tool.run(
            {
                "command": "nonexistentcommand123",
                "language": "bash",
            }
        )
        assert "command not found" in result or "not found" in result

    def test_command_with_whitespace(self, shell_tool):
        """Test handling of commands with significant whitespace."""
        # Create temporary files with and without spaces in names
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = os.path.join(temp_dir, "no_spaces.txt")
            file2 = os.path.join(temp_dir, "with spaces.txt")

            with open(file1, "w") as f:
                f.write("file1 content")
            with open(file2, "w") as f:
                f.write("file2 content")

            result = shell_tool.run(
                {
                    "command": f'ls -la "{temp_dir}"',
                    "language": "bash",
                }
            )
            assert "no_spaces.txt" in result
            assert "with spaces.txt" in result
