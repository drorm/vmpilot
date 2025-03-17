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
from vmpilot.git_track import GitConfig, GitStatus, GitTracker

logger = logging.getLogger(__name__)


class Exchange:
    """Represents a single exchange between user and LLM, with Git tracking."""
    
    def __init__(self, chat_id: str, user_message: Union[Dict, HumanMessage], git_enabled: bool = True, 
                 git_config: Optional[GitConfig] = None):
        """Initialize a new exchange.
        
        Args:
            chat_id: Identifier for the chat this exchange belongs to
            user_message: The user's message that initiated this exchange
            git_enabled: Whether Git tracking is enabled for this exchange
            git_config: Configuration for Git tracking (if None, default config is used)
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
        self.git_enabled = git_enabled
        
        # Initialize Git tracker if enabled
        self.git_tracker = GitTracker(config=git_config) if git_enabled else None
        
        # Check Git repo status at start of exchange
        self.check_git_status()
    
    def check_git_status(self) -> bool:
        """Check if Git repo is clean, warn if not.
        
        Returns:
            True if repository is clean or Git tracking is disabled, False otherwise.
        """
        if not self.git_enabled or not self.git_tracker:
            return True
            
        status = self.git_tracker.get_repo_status()
        if status == GitStatus.DIRTY:
            # Just log for now, later could integrate with UI to prompt user
            logger.warning("Git repository has uncommitted changes before LLM operation")
            return False
        return True
    
    def complete(self, assistant_message: Union[Dict, AIMessage], tool_calls: Optional[List] = None) -> "Exchange":
        """Complete the exchange with assistant response and handle Git commit.
        
        Args:
            assistant_message: The assistant's response message
            tool_calls: List of tool calls made during this exchange
            
        Returns:
            Self for method chaining
        """
        # Handle different assistant message formats
        if isinstance(assistant_message, dict):
            self.assistant_message = AIMessage(content=assistant_message.get("content", ""))
        else:
            self.assistant_message = assistant_message
            
        self.tool_calls = tool_calls or []
        self.completed_at = datetime.now()
        
        # Commit any changes the LLM made
        self.commit_changes()
        
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
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.get_duration(),
            "tool_call_count": self.get_tool_call_count(),
            "git_enabled": self.git_enabled,
            "git_changes_committed": self.commit_changes() if self.git_enabled else False,
        }