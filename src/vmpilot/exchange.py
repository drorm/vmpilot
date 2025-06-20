"""
Exchange module for VMPilot.

This module defines the Exchange class, which represents a single exchange between 
a user and the LLM, with Git tracking capabilities.

Terminology:
- Message: A single message in the OpenAI format (role + content)
- Exchange: A user message + the LLM's response (including any tool calls)
- Chat: A series of exchanges, identified by a chat_id
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from vmpilot.config import GitConfig, config
from vmpilot.git_track import GitStatus, GitTracker

logger = logging.getLogger(__name__)


class Exchange:
    """Represents a single exchange between user and LLM, with Git tracking."""

    def __init__(
        self,
        chat_id: str,
        user_message: Dict[str, Any],
        output_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """Initialize a new exchange.

        Args:
            chat_id: Identifier for the chat this exchange belongs to
            user_message: The user's message that initiated this exchange
            output_callback: Optional callback for user messages
        """
        self.output_callback = output_callback
        self.chat_id = chat_id

        self.user_message = user_message
        self.assistant_message: Dict[str, Any] | None = None
        self.tool_calls: list[dict[str, Any]] = []
        self.started_at = datetime.now()
        self.completed_at: datetime | None = None

        # Use provided git_enabled or fall back to config
        self.git_enabled = config.git_config.enabled
        logger.debug(
            f"Git tracking enabled: {self.git_enabled}, config.git_config: {config.git_config}"
        )

        # Initialize Git tracker if enabled
        self.git_tracker = GitTracker() if self.git_enabled else None

        # Check Git repo status at start of exchange
        self.check_git_status()
        logger.info(f"New exchange started for chat_id: {self.chat_id}")

    def check_git_status(self) -> bool:
        """Check if Git repo is clean, warn if not.

        Returns:
            True if repository is clean or Git tracking is disabled, False otherwise.
        """
        if not self.git_enabled or not self.git_tracker:
            return True

        status = self.git_tracker.get_repo_status()
        logger.debug(f"Git repository status: {status.name}")
        if status == GitStatus.DIRTY:
            # Check dirty_repo_action from config
            dirty_action = config.git_config.dirty_repo_action.lower()

            # For 'stop' mode, halt processing
            if dirty_action == "stop":
                # Return False to indicate dirty repo
                return False
            elif dirty_action == "stash":
                # Stash uncommitted changes
                logger.info("Attempting to stash uncommitted changes...")
                stash_success = self.git_tracker.stash_changes(
                    "VMPilot: Auto-stashed changes before LLM operation"
                )
                if stash_success:
                    logger.info("Successfully stashed uncommitted changes")
                    if self.output_callback:
                        stash_message = "I've stashed your uncommitted changes to ensure a clean working environment."
                        self.output_callback({"type": "text", "text": stash_message})
                    return True
                else:
                    logger.warning("Failed to stash uncommitted changes")
                    return False
            else:
                # Default behavior for unknown actions
                logger.debug(
                    f"Unknown dirty_repo_action '{dirty_action}'. Git repository has uncommitted changes."
                )
                return False
        return True

    def complete(
        self,
        assistant_message: Dict[str, Any],
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> "Exchange":
        """Complete the exchange with assistant response and handle Git commit.

        Args:
            assistant_message: The assistant's response message
            tool_calls: List of tool calls made during this exchange

        Returns:
            Self for method chaining
        """
        self.assistant_message = assistant_message

        self.tool_calls = tool_calls or []
        self.completed_at = datetime.now()

        # Commit any changes the LLM made
        try:
            self.commit_changes()
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            # Continue with the exchange even if commit fails

        return self

    def commit_changes(self) -> bool:
        """Commit any changes made during this exchange.

        Returns:
            True if changes were committed successfully, False otherwise.
        """
        if not self.git_enabled or not self.git_tracker:
            return False

        if self.git_tracker.get_repo_status() == GitStatus.DIRTY:
            # Use GitTracker's auto_commit_changes which handles commit message generation
            success, commit_msg = self.git_tracker.auto_commit_changes()
            if success:
                # log the first line of the commit message
                first_line = commit_msg.split("\n")[0]
                logger.info(f"Committed LLM-generated changes: {first_line}")
                return True
            else:
                logger.warning(f"Failed to commit changes: {commit_msg}")
                return False
        return False

    def to_messages(self) -> List[Dict[str, Any]]:
        """Convert exchange to message format for conversation state.

        Returns:
            List of messages in this exchange
        """
        messages = [self.user_message]
        if self.assistant_message:
            messages.append(self.assistant_message)
        return messages

    def get_duration(self) -> float | None:
        """Get the duration of this exchange in seconds.

        Returns:
            float | None: Duration in seconds, or None if exchange is not completed
        """
        if not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def get_tool_call_count(self) -> int:
        """Get the number of tool calls made during this exchange.

        Returns:
            Number of tool calls
        """
        return len(self.tool_calls)

    def get_exchange_summary(self) -> Dict[str, Any]:
        """Get a summary of this exchange.

        Returns:
            Dictionary with exchange summary information
        """
        return {
            "chat_id": self.chat_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_seconds": self.get_duration(),
            "tool_call_count": self.get_tool_call_count(),
            "git_enabled": self.git_enabled,
            "git_changes_committed": (
                self.commit_changes() if self.git_enabled else False
            ),
        }
