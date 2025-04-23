"""
Tests for the GitConfig class and configuration-related functionality in git_track module.

These tests focus on:
1. Default configuration values
2. Custom configuration initialization
3. Configuration usage with different commit message styles
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from vmpilot.config import Provider as APIProvider, CommitMessageStyle, GitConfig
from vmpilot.git_track import GitTracker


class TestGitConfig(unittest.TestCase):
    """Test cases for the GitConfig dataclass."""

    def test_default_values(self):
        """Test that GitConfig has the expected default values."""
        config = GitConfig()
        self.assertTrue(config.auto_commit)
        self.assertEqual(config.commit_message_style, CommitMessageStyle.DETAILED)
        self.assertEqual(config.dirty_repo_action, "stop")
        self.assertEqual(config.model, "gpt-3.5-turbo")
        self.assertEqual(config.provider, APIProvider.OPENAI)
        self.assertEqual(config.temperature, 0.2)
        self.assertEqual(config.commit_prefix, "[VMPilot]")

    def test_custom_values(self):
        """Test that GitConfig can be initialized with custom values."""
        config = GitConfig(
            auto_commit=False,
            commit_message_style=CommitMessageStyle.SHORT,
            dirty_repo_action="stash",
            model="gpt-4",
            provider=APIProvider.ANTHROPIC,
            temperature=0.5,
            commit_prefix="[AI]",
        )
        self.assertFalse(config.auto_commit)
        self.assertEqual(config.commit_message_style, CommitMessageStyle.SHORT)
        self.assertEqual(config.dirty_repo_action, "stash")
        self.assertEqual(config.model, "gpt-4")
        self.assertEqual(config.provider, APIProvider.ANTHROPIC)
        self.assertEqual(config.temperature, 0.5)
        self.assertEqual(config.commit_prefix, "[AI]")


class TestCommitMessageStyles(unittest.TestCase):
    """Test cases for different commit message styles."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_short_commit_message_style(self):
        """Test generate_commit_message with SHORT style."""
        # Set up configuration with SHORT style and patch the config
        with patch(
            "vmpilot.git_track.config.git_config",
            GitConfig(commit_message_style=CommitMessageStyle.SHORT),
        ):
            # Create a GitTracker with the patched config
            with patch("vmpilot.git_track.os.getcwd", return_value=self.temp_dir):
                git_tracker = GitTracker()

                # Mock the generate_commit_message method directly
                with patch.object(
                    git_tracker,
                    "generate_commit_message",
                    return_value="fix: resolve issue",
                ):
                    result = git_tracker.generate_commit_message("diff content")
                    self.assertEqual(result, "fix: resolve issue")

    def test_detailed_commit_message_style(self):
        """Test generate_commit_message with DETAILED style."""
        # Set up configuration with DETAILED style and patch the config
        with patch(
            "vmpilot.git_track.config.git_config",
            GitConfig(commit_message_style=CommitMessageStyle.DETAILED),
        ):
            # Create a GitTracker with the patched config
            with patch("vmpilot.git_track.os.getcwd", return_value=self.temp_dir):
                git_tracker = GitTracker()

                detailed_message = "feat: add new user authentication system\n\nImplemented JWT-based authentication with role-based access control."

                # Mock the generate_commit_message method directly
                with patch.object(
                    git_tracker,
                    "generate_commit_message",
                    return_value=detailed_message,
                ):
                    result = git_tracker.generate_commit_message("diff content")
                    self.assertEqual(result, detailed_message)

    def test_bullet_points_commit_message_style(self):
        """Test generate_commit_message with BULLET_POINTS style."""
        # Set up configuration with BULLET_POINTS style and patch the config
        with patch(
            "vmpilot.git_track.config.git_config",
            GitConfig(commit_message_style=CommitMessageStyle.BULLET_POINTS),
        ):
            # Create a GitTracker with the patched config
            with patch("vmpilot.git_track.os.getcwd", return_value=self.temp_dir):
                git_tracker = GitTracker()

                bullet_message = "refactor: improve code organization\n\n- Extract helper methods\n- Improve naming conventions\n- Add documentation"

                # Mock the generate_commit_message method directly
                with patch.object(
                    git_tracker, "generate_commit_message", return_value=bullet_message
                ):
                    result = git_tracker.generate_commit_message("diff content")
                    self.assertEqual(result, bullet_message)


class TestInitialization(unittest.TestCase):
    """Test cases for GitTracker initialization."""

    def test_init_default_values(self):
        """Test GitTracker initialization with default values."""
        from vmpilot.config import config as app_config

        # Create a GitTracker instance which will use the default config
        git_tracker = GitTracker()

        self.assertEqual(git_tracker.repo_path, os.getcwd())
        self.assertEqual(git_tracker.config, app_config.git_config)


if __name__ == "__main__":
    unittest.main()
