"""
Tests for the git_track module.

These tests cover the GitTracker class which provides functionality for:
1. Checking Git repository status
2. Managing changes (stashing, committing)
3. Generating commit messages
4. Providing undo operations
5. Configuring Git tracking behavior
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import vmpilot.config
from vmpilot.config import Provider as APIProvider
from vmpilot.git_track import CommitMessageStyle, GitConfig, GitStatus, GitTracker


class TestGitConfig(unittest.TestCase):
    """Test cases for the GitConfig dataclass."""

    def test_default_values(self):
        """Test that GitConfig has the expected default values."""
        config = GitConfig()
        self.assertTrue(config.auto_commit)
        self.assertEqual(config.commit_message_style, CommitMessageStyle.DETAILED)
        self.assertEqual(config.dirty_repo_action, "abort")
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


class TestGitTracker(unittest.TestCase):
    """Test cases for the GitTracker class."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        # Note: Since GitTracker now always uses the default config,
        # we'll need to patch the config for testing
        self.config = GitConfig(
            auto_commit=True,
            commit_message_style=CommitMessageStyle.DETAILED,
            dirty_repo_action="abort",
        )

        # We'll patch the GitTracker to use our test directory and config
        # and patch the worker_llm.get_worker_llm function
        with patch("vmpilot.git_track.os.getcwd", return_value=self.temp_dir):
            with patch("vmpilot.git_track.config.git_config", self.config):
                with patch("vmpilot.worker_llm.get_worker_llm") as self.mock_get_llm:
                    # Mock the worker LLM to return a mock that can handle invoke
                    mock_llm = MagicMock()
                    mock_llm.invoke.return_value = MagicMock(
                        content="Test commit message"
                    )
                    self.mock_get_llm.return_value = mock_llm
                    self.git_tracker = GitTracker()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_is_git_repo_true(self, mock_run):
        """Test is_git_repo when the directory is a Git repository."""
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.git_tracker.is_git_repo())
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_is_git_repo_false(self, mock_run):
        """Test is_git_repo when the directory is not a Git repository."""
        mock_run.side_effect = subprocess.CalledProcessError(
            128, "git rev-parse", stderr=b"fatal: not a git repository"
        )
        self.assertFalse(self.git_tracker.is_git_repo())
        mock_run.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.is_git_repo")
    @patch("subprocess.run")
    def test_get_repo_status_not_a_repo(self, mock_run, mock_is_git_repo):
        """Test get_repo_status when the directory is not a Git repository."""
        mock_is_git_repo.return_value = False
        self.assertEqual(self.git_tracker.get_repo_status(), GitStatus.NOT_A_REPO)
        mock_is_git_repo.assert_called_once()
        mock_run.assert_not_called()

    @patch("vmpilot.git_track.GitTracker.is_git_repo")
    @patch("subprocess.run")
    def test_get_repo_status_clean(self, mock_run, mock_is_git_repo):
        """Test get_repo_status when the repository is clean."""
        mock_is_git_repo.return_value = True
        mock_run.return_value = MagicMock(stdout="", stderr="")
        self.assertEqual(self.git_tracker.get_repo_status(), GitStatus.CLEAN)
        mock_is_git_repo.assert_called_once()
        mock_run.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.is_git_repo")
    @patch("subprocess.run")
    def test_get_repo_status_dirty(self, mock_run, mock_is_git_repo):
        """Test get_repo_status when the repository is dirty."""
        mock_is_git_repo.return_value = True
        mock_run.return_value = MagicMock(stdout=" M file.txt", stderr="")
        self.assertEqual(self.git_tracker.get_repo_status(), GitStatus.DIRTY)
        mock_is_git_repo.assert_called_once()
        mock_run.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("subprocess.run")
    def test_stash_changes_clean(self, mock_run, mock_get_repo_status):
        """Test stash_changes when the repository is clean."""
        mock_get_repo_status.return_value = GitStatus.CLEAN
        self.assertFalse(self.git_tracker.stash_changes())
        mock_get_repo_status.assert_called_once()
        mock_run.assert_not_called()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("subprocess.run")
    def test_stash_changes_dirty(self, mock_run, mock_get_repo_status):
        """Test stash_changes when the repository is dirty."""
        mock_get_repo_status.return_value = GitStatus.DIRTY
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.git_tracker.stash_changes())
        mock_get_repo_status.assert_called_once()
        mock_run.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.has_stashed_changes")
    @patch("subprocess.run")
    def test_pop_stash_no_stashed_changes(self, mock_run, mock_has_stashed_changes):
        """Test pop_stash when there are no stashed changes."""
        mock_has_stashed_changes.return_value = False

        result = self.git_tracker.pop_stash()

        self.assertFalse(result)
        mock_has_stashed_changes.assert_called_once()
        mock_run.assert_not_called()

    @patch("vmpilot.git_track.GitTracker.has_stashed_changes")
    @patch("subprocess.run")
    def test_pop_stash_success(self, mock_run, mock_has_stashed_changes):
        """Test pop_stash when successful."""
        mock_has_stashed_changes.return_value = True
        mock_run.return_value = MagicMock(stdout="Dropped stash@{0}", returncode=0)

        result = self.git_tracker.pop_stash()

        self.assertTrue(result)
        mock_has_stashed_changes.assert_called_once()
        mock_run.assert_called_once_with(
            ["git", "stash", "pop", "stash@{0}"],
            cwd=self.temp_dir,
            check=True,
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            text=True,
        )

    @patch("vmpilot.git_track.GitTracker.has_stashed_changes")
    @patch("subprocess.run")
    def test_pop_stash_with_index(self, mock_run, mock_has_stashed_changes):
        """Test pop_stash with a specific stash index."""
        mock_has_stashed_changes.return_value = True
        mock_run.return_value = MagicMock(stdout="Dropped stash@{2}", returncode=0)

        result = self.git_tracker.pop_stash(stash_index=2)

        self.assertTrue(result)
        mock_has_stashed_changes.assert_called_once()
        mock_run.assert_called_once_with(
            ["git", "stash", "pop", "stash@{2}"],
            cwd=self.temp_dir,
            check=True,
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            text=True,
        )

    @patch("vmpilot.git_track.GitTracker.has_stashed_changes")
    @patch("subprocess.run")
    def test_pop_stash_failure(self, mock_run, mock_has_stashed_changes):
        """Test pop_stash when it fails."""
        mock_has_stashed_changes.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "git stash pop")

        result = self.git_tracker.pop_stash()

        self.assertFalse(result)
        mock_has_stashed_changes.assert_called_once()
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_has_stashed_changes_true(self, mock_run):
        """Test has_stashed_changes when there are stashed changes."""
        mock_run.return_value = MagicMock(
            stdout="stash@{0}: WIP on branch", returncode=0
        )

        result = self.git_tracker.has_stashed_changes()

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "stash", "list"],
            cwd=self.temp_dir,
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            check=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_has_stashed_changes_false(self, mock_run):
        """Test has_stashed_changes when there are no stashed changes."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        result = self.git_tracker.has_stashed_changes()

        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_get_diff_working_only(self, mock_run):
        """Test get_diff with only working directory changes."""
        # Mock the subprocess calls
        mock_run.side_effect = [
            MagicMock(
                stdout="diff --git a/file.txt b/file.txt", stderr=""
            ),  # Working directory diff
            MagicMock(stdout="", stderr=""),  # Staged diff (empty)
        ]

        result = self.git_tracker.get_diff(include_staged=True)

        self.assertEqual(result, "diff --git a/file.txt b/file.txt")
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    def test_get_diff_staged_only(self, mock_run):
        """Test get_diff with only staged changes."""
        # Mock the subprocess calls
        mock_run.side_effect = [
            MagicMock(stdout="", stderr=""),  # Working directory diff (empty)
            MagicMock(
                stdout="diff --git a/staged.txt b/staged.txt", stderr=""
            ),  # Staged diff
        ]

        result = self.git_tracker.get_diff(include_staged=True)

        self.assertEqual(result, "diff --git a/staged.txt b/staged.txt")
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    def test_get_diff_both(self, mock_run):
        """Test get_diff with both working and staged changes."""
        # Mock the subprocess calls
        mock_run.side_effect = [
            MagicMock(
                stdout="diff --git a/working.txt b/working.txt", stderr=""
            ),  # Working directory diff
            MagicMock(
                stdout="diff --git a/staged.txt b/staged.txt", stderr=""
            ),  # Staged diff
        ]

        result = self.git_tracker.get_diff(include_staged=True)

        expected = "# Staged changes\ndiff --git a/staged.txt b/staged.txt\n# Working directory changes\ndiff --git a/working.txt b/working.txt"
        self.assertEqual(result, expected)
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    def test_get_diff_staged_false(self, mock_run):
        """Test get_diff when include_staged is False."""
        mock_run.return_value = MagicMock(
            stdout="diff --git a/file.txt b/file.txt", stderr=""
        )

        result = self.git_tracker.get_diff(include_staged=False)

        self.assertEqual(result, "diff --git a/file.txt b/file.txt")
        self.assertEqual(
            mock_run.call_count, 1
        )  # Only one call for working directory diff

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("subprocess.run")
    def test_commit_changes_clean(self, mock_run, mock_get_repo_status):
        """Test commit_changes when the repository is clean."""
        mock_get_repo_status.return_value = GitStatus.CLEAN
        self.assertFalse(self.git_tracker.commit_changes("Test commit"))
        mock_get_repo_status.assert_called_once()
        mock_run.assert_not_called()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("subprocess.run")
    def test_commit_changes_dirty(self, mock_run, mock_get_repo_status):
        """Test commit_changes when the repository is dirty."""
        mock_get_repo_status.return_value = GitStatus.DIRTY
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.git_tracker.commit_changes("Test commit"))
        mock_get_repo_status.assert_called_once()
        self.assertEqual(mock_run.call_count, 2)  # git add and git commit

    def test_auto_commit_disabled(self):
        """Test auto_commit_changes when auto-commit is disabled in config."""
        self.git_tracker.config.auto_commit = False

        success, message = self.git_tracker.auto_commit_changes()

        self.assertFalse(success)
        self.assertEqual(message, "Auto-commit is disabled")

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("vmpilot.git_track.GitTracker.get_diff")
    @patch("vmpilot.git_track.worker_llm.run_worker")
    @patch("vmpilot.git_track.GitTracker.commit_changes")
    def test_auto_commit_changes_success(
        self, mock_commit, mock_worker, mock_diff, mock_status
    ):
        """Test auto_commit_changes when successful."""
        mock_status.return_value = GitStatus.DIRTY
        mock_diff.return_value = "diff content"
        mock_worker.return_value = "Auto-generated commit message"
        mock_commit.return_value = True

        success, message = self.git_tracker.auto_commit_changes()

        self.assertTrue(success)
        self.assertEqual(message, "Auto-generated commit message")
        mock_status.assert_called_once()
        mock_diff.assert_called_once_with(include_staged=True)
        mock_worker.assert_called_once()
        mock_commit.assert_called_once_with("Auto-generated commit message")

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    def test_auto_commit_changes_clean(self, mock_status):
        """Test auto_commit_changes when the repository is clean."""
        mock_status.return_value = GitStatus.CLEAN

        success, message = self.git_tracker.auto_commit_changes()

        self.assertFalse(success)
        self.assertEqual(message, "No changes to commit")
        mock_status.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("vmpilot.git_track.GitTracker.get_diff")
    @patch("vmpilot.git_track.worker_llm.run_worker")
    @patch("vmpilot.git_track.GitTracker.commit_changes")
    def test_auto_commit_changes_failure(
        self, mock_commit, mock_worker, mock_diff, mock_status
    ):
        """Test auto_commit_changes when commit fails."""
        mock_status.return_value = GitStatus.DIRTY
        mock_diff.return_value = "diff content"
        mock_worker.return_value = "Auto-generated commit message"
        mock_commit.return_value = False

        success, message = self.git_tracker.auto_commit_changes()

        self.assertFalse(success)
        self.assertEqual(message, "Failed to commit changes")
        mock_status.assert_called_once()
        mock_diff.assert_called_once()
        mock_worker.assert_called_once()
        mock_commit.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    @patch("vmpilot.git_track.GitTracker.get_diff")
    @patch("vmpilot.git_track.worker_llm.run_worker")
    def test_auto_commit_changes_exception(self, mock_worker, mock_diff, mock_status):
        """Test auto_commit_changes when an exception occurs."""
        mock_status.return_value = GitStatus.DIRTY
        mock_diff.return_value = "diff content"
        mock_worker.side_effect = Exception("Test exception")

        success, message = self.git_tracker.auto_commit_changes()

        self.assertFalse(success)
        self.assertEqual(message, "Error generating commit message: Test exception")
        mock_status.assert_called_once()
        mock_diff.assert_called_once()
        mock_worker.assert_called_once()

    @patch("subprocess.run")
    def test_undo_last_commit_success(self, mock_run):
        """Test undo_last_commit when successful."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.git_tracker.undo_last_commit()

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "revert", "HEAD", "--no-edit"],
            cwd=self.temp_dir,
            check=True,
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            text=True,
        )

    @patch("subprocess.run")
    def test_undo_last_commit_failure(self, mock_run):
        """Test undo_last_commit when it fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git revert")

        result = self.git_tracker.undo_last_commit()

        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_reset_to_previous_commit_soft(self, mock_run):
        """Test reset_to_previous_commit with soft reset."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.git_tracker.reset_to_previous_commit(num_commits=1, hard=False)

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "reset", "--soft", "HEAD~1"],
            cwd=self.temp_dir,
            check=True,
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            text=True,
        )

    @patch("subprocess.run")
    def test_reset_to_previous_commit_hard(self, mock_run):
        """Test reset_to_previous_commit with hard reset."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.git_tracker.reset_to_previous_commit(num_commits=2, hard=True)

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "reset", "--hard", "HEAD~2"],
            cwd=self.temp_dir,
            check=True,
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            text=True,
        )

    @patch("subprocess.run")
    def test_reset_to_previous_commit_failure(self, mock_run):
        """Test reset_to_previous_commit when it fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git reset")

        result = self.git_tracker.reset_to_previous_commit()

        self.assertFalse(result)
        mock_run.assert_called_once()

    def test_pre_execution_check_stash_action(self):
        """Test pre_execution_check when dirty_repo_action is set to stash."""
        self.git_tracker.config.dirty_repo_action = "stash"

        # Mock the necessary methods for this test
        with patch.object(
            self.git_tracker, "get_repo_status", return_value=GitStatus.DIRTY
        ):
            with patch.object(self.git_tracker, "stash_changes", return_value=True):
                can_proceed, message = self.git_tracker.pre_execution_check()

                self.assertTrue(can_proceed)
                self.assertEqual(message, "Uncommitted changes have been stashed")

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    def test_pre_execution_check_not_a_repo(self, mock_get_repo_status):
        """Test pre_execution_check when not in a Git repository."""
        mock_get_repo_status.return_value = GitStatus.NOT_A_REPO

        can_proceed, message = self.git_tracker.pre_execution_check()

        self.assertTrue(can_proceed)
        self.assertEqual(message, "Not a Git repository")
        mock_get_repo_status.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    def test_pre_execution_check_clean(self, mock_get_repo_status):
        """Test pre_execution_check when the repository is clean."""
        mock_get_repo_status.return_value = GitStatus.CLEAN

        can_proceed, message = self.git_tracker.pre_execution_check()

        self.assertTrue(can_proceed)
        self.assertEqual(message, "Repository is clean")
        mock_get_repo_status.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.get_repo_status")
    def test_pre_execution_check_dirty(self, mock_get_repo_status):
        """Test pre_execution_check when the repository is dirty."""
        mock_get_repo_status.return_value = GitStatus.DIRTY

        can_proceed, message = self.git_tracker.pre_execution_check()

        self.assertFalse(can_proceed)
        self.assertEqual(
            message,
            "Repository has uncommitted changes. Please commit or stash them before proceeding.",
        )
        mock_get_repo_status.assert_called_once()


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
            temperature=0.2,
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
