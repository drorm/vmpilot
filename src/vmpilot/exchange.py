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
from typing import Any, Dict, List, Optional, Union

from langchain_core.messages import AIMessage, HumanMessage

from vmpilot.agent_memory import save_conversation_state
from vmpilot.config import GitConfig, config
from vmpilot.git_track import GitStatus, GitTracker

logger = logging.getLogger(__name__)


class Exchange:
    """Represents a single exchange between user and LLM, with Git tracking."""

    def __init__(
        self,
        chat_id: str,
        user_message: Union[Dict, HumanMessage],
    ):
        """Initialize a new exchange.

        Args:
            chat_id: Identifier for the chat this exchange belongs to
            user_message: The user's message that initiated this exchange
        """
        self.chat_id = chat_id

        # Handle different user message formats
        if isinstance(user_message, dict):
            self.user_message = HumanMessage(content=user_message.get("content", ""))
        else:
            self.user_message = user_message

        self.assistant_message = None
        self.tool_calls = []
        self.started_at = datetime.now()
        self.completed_at = None

        # Use provided git_enabled or fall back to config
        self.git_enabled = config.git_config.enabled
        logger.info(
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
        logger.info(f"Git repository status: {status.name}")
        if status == GitStatus.DIRTY:
            # Check dirty_repo_action from config
            dirty_action = config.git_config.dirty_repo_action.lower()

            # For 'stop' mode, halt processing
            if dirty_action == "stop":
                logger.warning(
                    "Git repository has uncommitted changes before LLM operation"
                )
                # Return False to indicate dirty repo
                return False
            # For future 'stash' implementation
            elif dirty_action == "stash":
                logger.warning(
                    "Git repository has uncommitted changes. Stash functionality not yet implemented."
                )
                return False
            else:
                # Default behavior for unknown actions
                logger.warning(
                    f"Unknown dirty_repo_action '{dirty_action}'. Git repository has uncommitted changes."
                )
                return False
        return True

    def complete(
        self,
        assistant_message: Union[Dict, AIMessage],
        tool_calls: Optional[List] = None,
    ) -> "Exchange":
        """Complete the exchange with assistant response and handle Git commit.

        Args:
            assistant_message: The assistant's response message
            tool_calls: List of tool calls made during this exchange

        Returns:
            Self for method chaining
        """
        # Handle different assistant message formats
        if isinstance(assistant_message, dict):
            self.assistant_message = AIMessage(
                content=assistant_message.get("content", "")
            )
        else:
            self.assistant_message = assistant_message

        self.tool_calls = tool_calls or []
        self.completed_at = datetime.now()

        # Commit any changes the LLM made
        try:
            self.commit_changes()
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            # Continue with the exchange even if commit fails

        # Save conversation state
        self.save_state()

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
                logger.info(f"Committed LLM-generated changes: {commit_msg}")
                return True
            else:
                logger.warning(f"Failed to commit changes: {commit_msg}")
                return False
        return False

    def save_state(self) -> None:
        """Save the conversation state."""
        # Call existing save_conversation_state with our data
        save_conversation_state(self.chat_id, self.to_messages(), {})
        logger.debug(f"Saved conversation state for chat_id: {self.chat_id}")

    def to_messages(self) -> List:
        """Convert exchange to message format for conversation state.

        Returns:
            List of messages in this exchange
        """
        messages = [self.user_message]
        if self.assistant_message:
            messages.append(self.assistant_message)
        return messages

    def get_duration(self) -> float:
        """Get the duration of this exchange in seconds.

        Returns:
            Duration in seconds, or None if exchange is not completed
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
