"""
Tests for the git_track module.

These tests cover the GitTracker class which provides functionality for:
1. Checking Git repository status
2. Managing changes (stashing, committing)
3. Generating commit messages
4. Providing undo operations
5. Configuring Git tracking behavior
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import vmpilot.config
from vmpilot.config import CommitMessageStyle, GitConfig
from vmpilot.config import Provider as APIProvider
from vmpilot.git_track import GitStatus, GitTracker


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
            dirty_repo_action="stop",
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
        """Test get_repo_status when the repository is dirty with modified files."""
        mock_is_git_repo.return_value = True
        mock_run.return_value = MagicMock(stdout=" M file.txt", stderr="")
        self.assertEqual(self.git_tracker.get_repo_status(), GitStatus.DIRTY)
        mock_is_git_repo.assert_called_once()
        mock_run.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.is_git_repo")
    @patch("subprocess.run")
    def test_get_repo_status_untracked_only(self, mock_run, mock_is_git_repo):
        """Test get_repo_status when the repository has only untracked files."""
        mock_is_git_repo.return_value = True
        mock_run.return_value = MagicMock(
            stdout="?? new_file.txt\n?? another_file.py", stderr=""
        )
        self.assertEqual(self.git_tracker.get_repo_status(), GitStatus.UNTRACKED_ONLY)
        mock_is_git_repo.assert_called_once()
        mock_run.assert_called_once()

    @patch("vmpilot.git_track.GitTracker.is_git_repo")
    @patch("subprocess.run")
    def test_get_repo_status_mixed_changes(self, mock_run, mock_is_git_repo):
        """Test get_repo_status when the repository has both modified and untracked files."""
        mock_is_git_repo.return_value = True
        mock_run.return_value = MagicMock(
            stdout=" M file.txt\n?? new_file.txt", stderr=""
        )
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

    def test_auto_stash_changes_untracked_only(self):
        """Test auto_stash_changes when repository has only untracked files."""
        # Mock the get_repo_status method to return UNTRACKED_ONLY
        with patch.object(
            self.git_tracker, "get_repo_status", return_value=GitStatus.UNTRACKED_ONLY
        ):
            success, message = self.git_tracker.auto_stash_changes()

            self.assertTrue(success)
            self.assertEqual(
                message, "Repository has only untracked files (considered clean)"
            )

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
    def test_pre_execution_check_untracked_only(self, mock_get_repo_status):
        """Test pre_execution_check when the repository has only untracked files."""
        mock_get_repo_status.return_value = GitStatus.UNTRACKED_ONLY

        can_proceed, message = self.git_tracker.pre_execution_check()

        self.assertTrue(can_proceed)
        self.assertEqual(
            message, "Repository has only untracked files (considered clean)"
        )
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
