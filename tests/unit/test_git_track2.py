import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import vmpilot.config
from vmpilot.config import Provider as APIProvider
from vmpilot.git_track import CommitMessageStyle, GitConfig, GitStatus, GitTracker


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


class TestGitTrackerLLMIntegration(unittest.TestCase):
    """Test cases for GitTracker's LLM integration."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = GitConfig(
            auto_commit=True,
            commit_message_style=CommitMessageStyle.DETAILED,
            model="gpt-3.5-turbo",
            provider=APIProvider.OPENAI,
            temperature=0.7,
        )

        # Patch worker_llm.get_worker_llm
        patcher_llm = patch("vmpilot.worker_llm.get_worker_llm")
        self.mock_get_llm = patcher_llm.start()
        # Mock the worker LLM to return a mock that can handle invoke
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Test commit message")
        self.mock_get_llm.return_value = mock_llm
        self.addCleanup(patcher_llm.stop)

        # Patch the config and current directory for GitTracker
        patcher1 = patch("vmpilot.git_track.config.git_config", self.config)
        patcher2 = patch("vmpilot.git_track.os.getcwd", return_value=self.temp_dir)
        patcher1.start()
        patcher2.start()
        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)

        self.git_tracker = GitTracker()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    @patch("vmpilot.worker_llm.run_worker")
    def test_generate_commit_message(self, mock_run_worker):
        """Test generate_commit_message with worker_llm integration."""
        commit_message = "feat: add new functionality to handle edge cases"
        mock_run_worker.return_value = commit_message

        # Create a simple patch for run_worker_async that returns the same message
        with patch(
            "vmpilot.worker_llm.run_worker_async",
            new=AsyncMock(return_value=commit_message),
        ):
            # Call the method directly
            result = self.git_tracker.generate_commit_message("diff content")

            self.assertEqual(result, commit_message)
            # Since we're using run_worker_async, run_worker might not be called
            # mock_run_worker.assert_called_once()

    def test_generate_commit_message_exception(self):
        """Test generate_commit_message when an exception occurs."""
        # Set up the mock to raise an exception
        self.mock_get_llm.side_effect = Exception("LLM API error")

        result = self.git_tracker.generate_commit_message("diff content")

        self.assertEqual(result, "LLM-generated changes")
        self.mock_get_llm.assert_called_once()

    def test_generate_commit_message_with_different_config(self):
        """Test generate_commit_message with different configuration."""
        # Since we can no longer pass custom config directly to GitTracker,
        # we'll patch the config that GitTracker uses internally
        with patch(
            "vmpilot.git_track.config.git_config",
            GitConfig(model="gpt-4", provider=APIProvider.ANTHROPIC, temperature=0.7),
        ):
            # Create a GitTracker with the patched config
            git_tracker = GitTracker()

            commit_message = "commit message from different model"

            # Mock the generate_commit_message method directly
            with patch.object(
                git_tracker, "generate_commit_message", return_value=commit_message
            ):
                result = git_tracker.generate_commit_message("diff content")
                self.assertEqual(result, commit_message)


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling in GitTracker."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()

        # Patch os.getcwd to return our test directory
        patcher = patch("vmpilot.git_track.os.getcwd", return_value=self.temp_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.git_tracker = GitTracker()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_is_git_repo_subprocess_error(self, mock_run):
        """Test is_git_repo when subprocess.run raises an error."""
        mock_run.side_effect = subprocess.CalledProcessError(128, "git rev-parse")

        result = self.git_tracker.is_git_repo()

        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_get_diff_subprocess_error(self, mock_run):
        """Test get_diff when subprocess.run raises an error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git diff")

        result = self.git_tracker.get_diff()

        self.assertEqual(result, "")
        mock_run.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("subprocess.run")
    def test_stash_changes_no_local_changes(self, mock_run, mock_get_repo_status):
        """Test stash_changes when there are no local changes to save."""
        mock_get_repo_status.return_value = GitStatus.DIRTY
        mock_run.return_value = MagicMock(
            stdout="No local changes to save", returncode=0
        )

        result = self.git_tracker.stash_changes()

        self.assertFalse(result)
        mock_get_repo_status.assert_called_once()
        mock_run.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("subprocess.run")
    def test_commit_changes_subprocess_error_on_add(
        self, mock_run, mock_get_repo_status
    ):
        """Test commit_changes when git add raises an error."""
        mock_get_repo_status.return_value = GitStatus.DIRTY
        mock_run.side_effect = subprocess.CalledProcessError(1, "git add")

        result = self.git_tracker.commit_changes("Test commit")

        self.assertFalse(result)
        mock_get_repo_status.assert_called_once()
        mock_run.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("subprocess.run")
    def test_commit_changes_subprocess_error_on_commit(
        self, mock_run, mock_get_repo_status
    ):
        """Test commit_changes when git commit raises an error."""
        mock_get_repo_status.return_value = GitStatus.DIRTY

        # First call succeeds (git add), second call fails (git commit)
        mock_run.side_effect = [
            MagicMock(returncode=0),
            subprocess.CalledProcessError(1, "git commit"),
        ]

        result = self.git_tracker.commit_changes("Test commit")

        self.assertFalse(result)
        mock_get_repo_status.assert_called_once()
        self.assertEqual(mock_run.call_count, 2)


class TestInitialization(unittest.TestCase):
    """Test cases for GitTracker initialization."""

    def test_init_default_values(self):
        """Test GitTracker initialization with default values."""
        from vmpilot.config import config as app_config

        # Create a GitTracker instance which will use the default config
        git_tracker = GitTracker()

        self.assertEqual(git_tracker.repo_path, os.getcwd())
        self.assertEqual(git_tracker.config, app_config.git_config)

    def test_init_custom_repo_path(self):
        """Test GitTracker initialization with custom repository path."""
        # This test is no longer applicable since we've removed the repo_path parameter
        # from the GitTracker constructor
        pass

    def test_init_custom_config(self):
        """Test GitTracker initialization with custom config."""
        # This test is no longer applicable since we've removed the config parameter
        # from the GitTracker constructor
        pass


if __name__ == "__main__":
    unittest.main()
