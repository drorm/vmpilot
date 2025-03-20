"""
LLM Git Track - A utility for tracking LLM-generated changes in git.

This module provides functionality to:
1. Check if a Git repository is clean before LLM operations
2. Commit LLM-generated changes with meaningful commit messages
3. Support stashing and restoring user changes
4. Provide undo mechanisms for LLM-generated changes
5. Configure Git tracking behavior
"""

import asyncio
import logging
import os
import subprocess
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import vmpilot.worker_llm as worker_llm
from vmpilot.config import CommitMessageStyle, GitConfig
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config

logger = logging.getLogger(__name__)

# System prompt for commit message generation
COMMIT_MESSAGE_SYSTEM_PROMPT = """You are a commit message generator for an AI assistant called VMPilot.
Your task is to analyze Git diffs and generate concise, informative commit messages.

Your commit messages should:
1. Start with a verb in the present tense (e.g., "Add", "Fix", "Update")
2. Be clear and descriptive
3. Focus on the "what" and "why" of the changes
4. Be no longer than 72 characters for the first line
5. Optionally include a more detailed description after a blank line

Example good commit messages:
- "Add user authentication to API endpoints"
- "Fix race condition in background task processing"
- "Refactor database connection handling for better error recovery"

Please analyze the provided Git diff and generate an appropriate commit message.
"""


class GitStatus(Enum):
    """Enum representing the status of the Git repository."""

    CLEAN = "clean"
    DIRTY = "dirty"
    NOT_A_REPO = "not_a_repo"


class GitTracker:
    """Class for tracking LLM-generated changes in Git."""

    def __init__(self):
        """Initialize the GitTracker."""
        self.repo_path = os.getcwd()
        # Use the global configuration
        self.config = config.git_config

    def is_git_repo(self) -> bool:
        """Check if the directory is a Git repository.

        Returns:
            True if the directory is a Git repository, False otherwise.
        """
        try:
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def get_repo_status(self) -> GitStatus:
        """Get the status of the Git repository.

        Returns:
            GitStatus enum indicating if the repo is clean, dirty, or not a repo.
        """
        if not self.is_git_repo():
            return GitStatus.NOT_A_REPO

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )

        return GitStatus.CLEAN if not result.stdout.strip() else GitStatus.DIRTY

    def stash_changes(self, message: str = "User changes before LLM request") -> bool:
        """Stash uncommitted changes.

        Args:
            message: Message to use for the stash.

        Returns:
            True if changes were stashed, False otherwise.
        """
        if self.get_repo_status() != GitStatus.DIRTY:
            logger.info("No changes to stash")
            return False

        try:
            result = subprocess.run(
                ["git", "stash", "push", "-m", message],
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Check if changes were actually stashed
            if "No local changes to save" in result.stdout:
                logger.info("No changes to stash")
                return False

            logger.info(f"Stashed changes: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stash changes: {e}")
            return False

    def pop_stash(self, stash_index: int = 0) -> bool:
        """Pop a stash.

        Args:
            stash_index: Index of the stash to pop. Default is 0 (most recent).

        Returns:
            True if stash was popped, False otherwise.
        """
        if not self.has_stashed_changes():
            logger.info("No stashed changes to pop")
            return False

        try:
            stash_ref = f"stash@{{{stash_index}}}" if stash_index > 0 else "stash@{0}"
            result = subprocess.run(
                ["git", "stash", "pop", stash_ref],
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info(f"Popped stash: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pop stash: {e}")
            return False

    def get_diff(self, include_staged: bool = True) -> str:
        """Get the diff of uncommitted changes.

        Args:
            include_staged: Whether to include staged changes in the diff.

        Returns:
            String containing the diff output.
        """
        try:
            # Get diff for working directory changes
            result = subprocess.run(
                ["git", "diff"],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            working_diff = result.stdout

            # Get diff for staged changes if requested
            staged_diff = ""
            if include_staged:
                result = subprocess.run(
                    ["git", "diff", "--staged"],
                    cwd=self.repo_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    text=True,
                )
                staged_diff = result.stdout

            # Combine diffs with headers if both exist
            if working_diff and staged_diff:
                return f"# Staged changes\n{staged_diff}\n# Working directory changes\n{working_diff}"
            elif staged_diff:
                return staged_diff
            else:
                return working_diff
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get diff: {e}")
            return ""

    def commit_changes(
        self, message: str, author: str = "VMPilot <vmpilot@ai.assistant>"
    ) -> bool:
        """Commit uncommitted changes.

        This method stages all changes in the working directory using 'git add .'
        and then commits them with the specified message and author.

        Args:
            message: Commit message.
            author: Author string in the format "Name <email>".

        Returns:
            True if changes were committed, False otherwise.
        """
        if self.get_repo_status() != GitStatus.DIRTY:
            logger.info("No changes to commit")
            return False

        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Commit with specified author
            result = subprocess.run(
                ["git", "commit", "--author", author, "-m", message],
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info(f"Committed changes: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes: {e}")
            return False

    def has_stashed_changes(self) -> bool:
        """Check if there are stashed changes.

        Returns:
            True if there are stashed changes, False otherwise.
        """
        try:
            result = subprocess.run(
                ["git", "stash", "list"],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check stashed changes: {e}")
            return False

    def _prepare_diff_prompt(self, diff: str) -> str:
        """Prepare a diff for use in an LLM prompt.

        Truncates the diff if it's too large and formats it as a code block.

        Args:
            diff: Git diff output to analyze.

        Returns:
            Formatted prompt string.
        """
        # Truncate diff if it's too large
        if len(diff) > 8000:
            logger.warning("Diff is too large, truncating")
            diff = diff[:8000] + "\n...[truncated]..."

        # Create prompt for the LLM
        return f"Here is the Git diff to analyze:\n\n```diff\n{diff}\n```"

    def generate_commit_message(self, diff: str) -> str:
        """Generate a commit message from a diff.

        Uses the worker LLM to analyze the diff and generate a meaningful commit message.

        Args:
            diff: Git diff output to analyze.

        Returns:
            Generated commit message.
        """
        try:
            prompt = self._prepare_diff_prompt(diff)

            # Run the async function in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            commit_message = loop.run_until_complete(
                worker_llm.run_worker_async(
                    prompt=prompt,
                    system_prompt=COMMIT_MESSAGE_SYSTEM_PROMPT,
                    model=self.config.model,
                    provider=self.config.provider,
                    temperature=self.config.temperature,
                )
            )
            loop.close()
            return commit_message
        except Exception as e:
            logger.error(f"Failed to generate commit message: {e}")
            return "LLM-generated changes"

    def auto_commit_changes(self) -> Tuple[bool, str]:
        """Automatically generate a commit message and commit changes.

        Returns:
            Tuple of (success, message) where success is True if changes were committed
            and message is the commit message or error message.
        """
        if not self.config.auto_commit:
            logger.info("Auto-commit is disabled")
            return (False, "Auto-commit is disabled")

        if self.get_repo_status() != GitStatus.DIRTY:
            return (False, "No changes to commit")

        try:
            diff = self.get_diff(include_staged=True)
            commit_msg = None

            # Generate a commit message - use synchronous approach for now.
            try:
                prompt = self._prepare_diff_prompt(diff)
                # Use synchronous worker
                commit_msg = worker_llm.run_worker(
                    prompt=prompt,
                    system_prompt=COMMIT_MESSAGE_SYSTEM_PROMPT,
                    model=self.config.model,
                    provider=self.config.provider,
                    temperature=self.config.temperature,
                )
            except Exception as e:
                logger.error(f"Failed to generate commit message: {e}")
                return (False, f"Error generating commit message: {e}")

            if commit_msg:
                success = self.commit_changes(commit_msg)
                return (success, commit_msg if success else "Failed to commit changes")
            else:
                return (False, "No commit message generated")
        except Exception as e:
            logger.error(f"Error in auto_commit_changes: {e}")
            return (False, str(e))

    def undo_last_commit(self) -> bool:
        """Undo the last commit using git revert.

        Returns:
            True if the last commit was reverted, False otherwise.
        """
        try:
            subprocess.run(
                ["git", "revert", "HEAD", "--no-edit"],
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to revert last commit: {e}")
            return False

    def reset_to_previous_commit(
        self, num_commits: int = 1, hard: bool = False
    ) -> bool:
        """Reset to a previous commit.

        Args:
            num_commits: Number of commits to go back.
            hard: Whether to use --hard (discard changes) or --soft (keep changes staged).

        Returns:
            True if reset was successful, False otherwise.
        """
        try:
            reset_type = "--hard" if hard else "--soft"
            commit_ref = f"HEAD~{num_commits}"

            subprocess.run(
                ["git", "reset", reset_type, commit_ref],
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reset to previous commit: {e}")
            return False

    def auto_stash_changes(self) -> Tuple[bool, str]:
        """Automatically stash changes if the repository is dirty.

        This is a higher-level method that checks if the repository is dirty
        and stashes changes if needed, based on configuration.

        Returns:
            Tuple of (success, message) where success is True if stashing was
            successful or not needed, and message is a status or error message.
        """
        status = self.get_repo_status()

        if status == GitStatus.NOT_A_REPO:
            return (True, "Not a Git repository")
        elif status == GitStatus.CLEAN:
            return (True, "Repository is clean")

        # Repository is dirty, stash changes
        stash_message = "VMPilot: Auto-stashed changes before LLM operation"
        stash_success = self.stash_changes(stash_message)

        if stash_success:
            return (True, "Uncommitted changes have been stashed")
        else:
            return (False, "Failed to stash uncommitted changes")

    def pre_execution_check(self) -> Tuple[bool, str]:
        """Check if the repository is clean before execution.

        If the repository is dirty, either stop or stash changes based on configuration.

        Returns:
            Tuple of (can_proceed, message) where can_proceed is True if execution can proceed
            and message is a status message or error message.
        """
        status = self.get_repo_status()

        if status == GitStatus.NOT_A_REPO:
            return (True, "Not a Git repository")
        elif status == GitStatus.CLEAN:
            return (True, "Repository is clean")
        else:
            # Repository is dirty, handle according to configuration
            if self.config.dirty_repo_action == "stash":
                return self.auto_stash_changes()
            else:  # Default is "stop"
                return (
                    False,
                    "Repository has uncommitted changes. Please commit or stash them before proceeding.",
                )
