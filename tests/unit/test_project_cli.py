"""
Tests for the project module focusing on CLI-related functionality.

This test file focuses on testing project.py functionality that's used in the CLI
but might not be adequately covered in other tests.
"""

import os
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add the src directory to the path to allow direct imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)
from vmpilot.project import Project


class TestProjectCli:
    """Tests for Project class focusing on CLI-specific functionality."""

    @pytest.fixture
    def mock_project_setup(self):
        """Setup a mock project with necessary patches."""
        with (
            patch("os.path.exists") as mock_exists,
            patch("os.path.isdir", return_value=True) as mock_isdir,
            patch("os.chdir") as mock_chdir,
            patch(
                "vmpilot.project.get_plugins_dir", return_value="/fake/plugins"
            ) as mock_plugins,
        ):

            # Configure mock_exists to handle different path checks
            def exists_side_effect(path):
                # Return True for the project directory
                if path == "/fake/project":
                    return True
                # Return False for .vmpilot structure by default
                if ".vmpilot" in path:
                    return False
                # Return False for user opt-out file
                if "~/.vmpilot/noproject.md" in path:
                    return False
                return False

            mock_exists.side_effect = exists_side_effect

            # Create a mock output callback to capture messages
            mock_callback = MagicMock()

            # Create the project instance
            project = Project(
                system_prompt_suffix="$PROJECT_ROOT=/fake/project",
                output_callback=mock_callback,
            )

            yield project, mock_exists, mock_isdir, mock_chdir, mock_callback, mock_plugins

    def test_check_project_structure(self, mock_project_setup):
        """Test check_project_structure when structure doesn't exist."""
        project, mock_exists, mock_isdir, mock_chdir, mock_callback, mock_plugins = (
            mock_project_setup
        )

        # Configure mock_exists to return False for .vmpilot structure
        def exists_side_effect(path):
            if path == "/fake/project":
                return True
            if path == os.path.expanduser("~/.vmpilot/noproject.md"):
                return False
            if ".vmpilot" in path:
                return False
            return False

        mock_exists.side_effect = exists_side_effect

        # Call the method
        project.check_project_structure()

        # Verify that the output callback was called with a setup message
        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0][0]
        assert call_args["type"] == "text"
        assert "Project Setup" in call_args["text"]
        assert "standard_setup.sh" in call_args["text"]
        assert "skip_setup.sh" in call_args["text"]

        # Verify that finish_chat is set to True
        assert project.finish_chat is True

    def test_check_project_structure_with_opt_out(self, mock_project_setup):
        """Test check_project_structure when user has opted out."""
        project, mock_exists, mock_isdir, mock_chdir, mock_callback, mock_plugins = (
            mock_project_setup
        )

        # Configure mock_exists to return True for opt-out file and include the project path in the file
        def exists_side_effect(path):
            if path == os.path.expanduser("~/.vmpilot/noproject.md"):
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        # Mock the open function to return the project path in the opt-out file
        with patch("builtins.open", mock_open(read_data="/fake/project\n")):
            # Call the method
            project.check_project_structure()

            # Verify that the output callback was not called (user opted out)
            mock_callback.assert_not_called()

            # Verify that finish_chat remains False
            assert project.finish_chat is False

    def test_check_vmpilot_structure(self, mock_project_setup):
        """Test check_vmpilot_structure with different directory configurations."""
        project, mock_exists, mock_isdir, mock_chdir, mock_callback, mock_plugins = (
            mock_project_setup
        )

        # Case 1: No structure exists
        def exists_side_effect1(path):
            return False

        mock_exists.side_effect = exists_side_effect1
        result1 = project.check_vmpilot_structure()
        assert result1 is False

        # Case 1: Only .vmpilot exists, but not prompts or project.md
        def exists_side_effect2(path):
            return "/fake/project/.vmpilot" in path and "prompts" not in path

        mock_exists.side_effect = exists_side_effect2
        result2 = project.check_vmpilot_structure()
        assert result2 is False

        # Case 2: Complete structure exists
        def exists_side_effect3(path):
            return True

        mock_exists.side_effect = exists_side_effect3
        result3 = project.check_vmpilot_structure()
        assert result3 is True

    def test_change_to_project_dir_errors(self):
        """Test change_to_project_dir error handling."""
        # Mock the output callback
        mock_callback = MagicMock()
        project = Project(system_prompt_suffix="", output_callback=mock_callback)
        project.project_root = "/nonexistent/path"

        # Case 2: Not a directory
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.isdir", return_value=False),
        ):
            with pytest.raises(Exception) as excinfo:
                project.change_to_project_dir()
            assert "Not a directory" in str(excinfo.value)

        # Case 3: Permission denied
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.isdir", return_value=True),
            patch("os.chdir", side_effect=PermissionError("Permission denied")),
        ):
            with pytest.raises(Exception) as excinfo:
                project.change_to_project_dir()
            assert "Permission denied" in str(excinfo.value)
