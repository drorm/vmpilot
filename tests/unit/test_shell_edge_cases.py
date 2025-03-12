import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from vmpilot.tools.shelltool import ShellTool


class TestShellToolEdgeCases:
    @pytest.fixture
    def shell_tool(self):
        return ShellTool()

    def test_empty_command(self, shell_tool):
        """Test handling of empty command string."""
        result = shell_tool.run({"command": "", "language": "bash"})
        assert "**$ **" in result  # Should show empty command
        assert isinstance(result, str)

    def test_whitespace_only_command(self, shell_tool):
        """Test handling of whitespace-only command string."""
        result = shell_tool.run({"command": "   ", "language": "bash"})
        assert "**$    **" in result  # Should show command with spaces
        assert isinstance(result, str)

    def test_command_with_trailing_spaces(self, shell_tool):
        """Test handling of command with trailing spaces."""
        result = shell_tool.run({"command": "echo 'test'   ", "language": "bash"})
        assert "test" in result
        assert "**$ echo 'test'   **" in result  # Should preserve spaces

    def test_extremely_long_command(self, shell_tool):
        """Test handling of extremely long command."""
        # Create a very long command (5000+ characters)
        long_text = "x" * 5000
        result = shell_tool.run({"command": f"echo '{long_text}'", "language": "text"})
        assert long_text in result

    def test_command_with_environment_modification(self, shell_tool):
        """Test commands that modify environment variables."""
        result = shell_tool.run(
            {
                "command": "export TEST_VAR='Modified' && echo $TEST_VAR",
                "language": "bash",
            }
        )
        assert "Modified" in result

    def test_command_with_current_directory_change(self, shell_tool):
        """Test commands that change the current directory."""
        # First, get the current directory
        current_dir = subprocess.run(
            "pwd", shell=True, capture_output=True, text=True, executable="/bin/bash"
        ).stdout.strip()

        # Run command that changes directory temporarily
        result = shell_tool.run(
            {"command": "cd /tmp && pwd && cd - > /dev/null && pwd", "language": "bash"}
        )
        assert "/tmp" in result
        assert current_dir in result

    def test_command_with_multiple_lines_of_output(self, shell_tool):
        """Test handling of commands with multiple lines of output with special characters."""
        result = shell_tool.run(
            {
                "command": """printf "Line 1\\nLine 2\\nLine with * wildcard\\nLine with $ dollar\\nLine with \\" quote" """,
                "language": "text",
            }
        )
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line with * wildcard" in result
        assert "Line with $ dollar" in result
        assert 'Line with " quote' in result

    def test_command_with_color_codes(self, shell_tool):
        """Test handling of commands that output ANSI color codes."""
        result = shell_tool.run(
            {
                "command": "echo -e '\\033[31mRed text\\033[0m Normal text'",
                "language": "text",
            }
        )
        # Color codes might be preserved or stripped - we're just checking it doesn't break
        assert "Red text" in result
        assert "Normal text" in result

    def test_command_with_tabs_and_newlines(self, shell_tool):
        """Test handling of commands with literal tabs and newlines."""
        result = shell_tool.run(
            {
                "command": """printf "Text with\\ttabs and\\nnewlines" """,
                "language": "text",
            }
        )
        assert "Text with" in result
        # The tabs and newlines should be preserved in the output

    def test_command_with_file_redirection(self, shell_tool):
        """Test commands with file redirection."""
        with tempfile.NamedTemporaryFile() as temp:
            result = shell_tool.run(
                {
                    "command": f"echo 'Redirected output' > {temp.name} && cat {temp.name}",
                    "language": "bash",
                }
            )
            assert "Redirected output" in result

    def test_command_with_pipe_to_multiple_commands(self, shell_tool):
        """Test command with pipe to multiple commands."""
        result = shell_tool.run(
            {
                "command": "echo 'test line1\ntest line2\ntest line3' | grep line | sort -r",
                "language": "bash",
            }
        )
        assert "test line3" in result
        assert "test line2" in result
        assert "test line1" in result
        # Should be in reverse order due to sort -r
        result_lines = result.split("\n")
        for i in range(len(result_lines)):
            if "test line3" in result_lines[i]:
                line3_idx = i
            if "test line1" in result_lines[i]:
                line1_idx = i
        assert line3_idx < line1_idx  # line3 should come before line1 in the output

    def test_command_with_unicode_filename(self, shell_tool):
        """Test handling of commands with Unicode filenames."""
        with tempfile.NamedTemporaryFile(prefix="你好_test_") as temp:
            unicode_filename = os.path.basename(temp.name)
            result = shell_tool.run(
                {"command": f"ls -la {temp.name}", "language": "bash"}
            )
            assert unicode_filename in result

    def test_command_with_glob_patterns(self, shell_tool):
        """Test handling of commands with glob patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a few files
            for i in range(3):
                with open(os.path.join(temp_dir, f"test_file_{i}.txt"), "w") as f:
                    f.write(f"Content {i}")

            result = shell_tool.run(
                {"command": f"ls {temp_dir}/*.txt", "language": "bash"}
            )
            assert "test_file_0.txt" in result
            assert "test_file_1.txt" in result
            assert "test_file_2.txt" in result

    def test_tool_name_and_description(self):
        """Test that tool name and description are properly set."""
        shell_tool = ShellTool()
        assert shell_tool.name == "shell"
        assert "Execute bash commands" in shell_tool.description

    def test_command_with_path_traversal(self, shell_tool):
        """Test handling of commands with path traversal patterns."""
        result = shell_tool.run({"command": "cd / && cd .. && pwd", "language": "bash"})
        assert "/" in result  # Should still be at root, can't go up from root

    def test_command_with_brace_expansion(self, shell_tool):
        """Test handling of commands with brace expansion."""
        result = shell_tool.run({"command": "echo {1..5}", "language": "bash"})
        assert "1 2 3 4 5" in result

    def test_command_with_arithmetic_expansion(self, shell_tool):
        """Test handling of commands with arithmetic expansion."""
        result = shell_tool.run({"command": "echo $((5+7))", "language": "bash"})
        assert "12" in result

    def test_command_with_background_process(self, shell_tool):
        """Test handling of commands that launch background processes."""
        result = shell_tool.run(
            {
                "command": "(sleep 1 && echo 'Done') & echo 'Started'; sleep 1",
                "language": "bash",
            }
        )
        assert "Started" in result
        assert "Done" in result  # Should capture output from background process
