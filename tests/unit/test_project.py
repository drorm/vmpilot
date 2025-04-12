"""
Tests for the project module.
"""

import os
from unittest.mock import mock_open, patch

import pytest

from vmpilot.project import (
    PROJECT_MD,
    PROMPTS_DIR,
    VMPILOT_DIR,
    get_project_description,
)


@patch("vmpilot.project.get_project_root")
@patch("os.path.exists")
@patch("builtins.open", new_callable=mock_open, read_data="Test project content")
def test_get_project_description_exists(mock_file, mock_exists, mock_project_root):
    # Setup
    mock_project_root.return_value = "/fake/project/root"
    mock_exists.return_value = True

    # Execute
    result = get_project_description()

    # Verify
    assert "Test project content" in result
    expected_path = f"/fake/project/root/{VMPILOT_DIR}/{PROMPTS_DIR}/{PROJECT_MD}"
    mock_exists.assert_called_once_with(expected_path)
    mock_file.assert_called_once_with(expected_path, "r")


@patch("vmpilot.project.get_project_root")
@patch("os.path.exists")
def test_get_project_description_not_exists(mock_exists, mock_project_root):
    # Setup
    mock_project_root.return_value = "/fake/project/root"
    mock_exists.return_value = False

    # Execute
    result = get_project_description()

    # Verify
    assert result == ""
    expected_path = f"/fake/project/root/{VMPILOT_DIR}/{PROMPTS_DIR}/{PROJECT_MD}"
    mock_exists.assert_called_once_with(expected_path)


@patch("vmpilot.project.get_project_root")
@patch("os.path.exists")
@patch("builtins.open", side_effect=IOError("Test error"))
def test_get_project_description_error(mock_file, mock_exists, mock_project_root):
    # Setup
    mock_project_root.return_value = "/fake/project/root"
    mock_exists.return_value = True

    # Execute
    result = get_project_description()

    # Verify
    assert result == ""
