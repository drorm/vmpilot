import pytest

from vmpilot.tools.shelltool import ShellTool


class TestShellTool:
    @pytest.fixture
    def shell_tool(self):
        return ShellTool()

    def test_basic_command_execution(self, shell_tool):
        """Test basic command execution with echo."""
        result = shell_tool.run({"command": "echo 'Hello, World!'", "language": "bash"})
        # The output includes command echo and markdown formatting
        assert "Hello, World!" in result
        assert isinstance(result, str)

    def test_command_with_error(self, shell_tool):
        """Test handling of commands that produce errors."""
        result = shell_tool.run(
            {"command": "ls /nonexistent/directory", "language": "bash"}
        )
        assert "No such file or directory" in result

    def test_command_with_pipe(self, shell_tool):
        """Test command with pipe and filtering."""
        # Using a different approach to avoid the input text in command
        result = shell_tool.run(
            {
                "command": "printf 'apple\nbanana\ncherry\n' | grep banana",
                "language": "bash",
            }
        )
        assert "banana" in result
        assert "apple" not in result.split("```")[1]  # Check only command output
        assert "cherry" not in result.split("```")[1]  # Check only command output

    def test_command_with_multiple_commands(self, shell_tool):
        """Test execution of multiple commands in sequence."""
        result = shell_tool.run(
            {
                "command": "cd /tmp && touch test_file.txt && ls test_file.txt && rm test_file.txt",
                "language": "bash",
            }
        )
        assert "test_file.txt" in result
