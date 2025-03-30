"""
Chat management for VMPilot.
Handles chat IDs, project directories, and session management.
"""

import logging
import os
import re
import secrets
import string
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from . import config

logger = logging.getLogger(__name__)


class Chat:
    """
    Class to manage chat sessions, including IDs and project directories.
    """

    CHAT_ID_PREFIX = "Chat id"
    CHAT_ID_DELIMITER = ":"
    PROJECT_ROOT_PATTERNS = [
        r"\$PROJECT_ROOT=([^\s]+)",
    ]

    def __init__(
        self, chat_id=None, project_dir=None, messages=None, output_callback=None
    ):
        """
        Initialize a chat session.

        Args:
            chat_id: Optional chat ID. If not provided, one will be generated.
            project_dir: Optional project directory. If not provided, will use default_project.
            messages: Optional list of chat messages to extract information from.
            output_callback: Optional callback function for sending output.
        """
        self.project_dir = project_dir if project_dir else config.DEFAULT_PROJECT
        self.messages = messages or []
        self.output_callback = output_callback

        # Extract project directory from messages if provided
        if messages:
            self.extract_project_dir(messages)

        # Get or generate chat_id
        self.chat_id = self._get_or_generate_chat_id(chat_id, messages, output_callback)

        # Change to project directory for new chats
        self.change_to_project_dir()

        if self.chat_id:
            logger.debug(f"Using chat_id: {self.chat_id}")

    def _generate_chat_id(self) -> str:
        """Generate a new random chat ID."""
        import time

        # Add a timestamp prefix to ensure uniqueness
        timestamp = (
            int(time.time() * 1000) % 10000
        )  # Last 4 digits of current timestamp in ms
        random_part = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(8)
        )
        return f"{timestamp}{random_part}"

    def _get_or_generate_chat_id(
        self,
        provided_chat_id: Optional[str],
        messages: Optional[List[Dict[str, str]]],
        output_callback: Optional[Callable[[Dict], None]],
    ) -> str:
        """
        Get an existing chat_id from messages, use provided chat_id, or generate a new one.

        Args:
            provided_chat_id: Chat ID explicitly provided to the constructor
            messages: List of chat messages
            output_callback: Callback function for sending output

        Returns:
            Chat ID string
        """
        # If a chat_id was explicitly provided, use it
        if provided_chat_id:
            logger.info(f"Using provided chat_id: {provided_chat_id}")
            return provided_chat_id

        # If we have messages, try to extract from them
        if messages and len(messages) > 2:
            # Existing chat, try to extract chat_id from assistant messages
            for msg in messages:
                if msg["role"] == "assistant" and isinstance(msg["content"], str):
                    content_lines = msg["content"].split("\n")
                    if content_lines and content_lines[0].startswith(
                        self.CHAT_ID_PREFIX
                    ):
                        # Extract chat_id from the first line
                        parts = content_lines[0].split(self.CHAT_ID_DELIMITER, 1)
                        if len(parts) > 1:
                            extracted_id = parts[1].strip()
                            logger.debug(f"Extracted chat_id: {extracted_id}")
                            return extracted_id

            logger.warning("Could not extract chat_id from messages")

        # Generate a new chat_id
        new_chat_id = self._generate_chat_id()
        logger.debug(f"Generated new chat_id: {new_chat_id}")

        # Announce chat ID if callback is provided
        if output_callback:
            output_callback(
                {
                    "type": "text",
                    "text": f"{self.CHAT_ID_PREFIX} {self.CHAT_ID_DELIMITER}{new_chat_id}\n\n",
                }
            )

        return new_chat_id

    def extract_project_dir(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Extract project directory from system message if present.

        Args:
            messages: List of chat messages

        Returns:
            Project directory if found, None otherwise
        """
        # Look for system message
        for msg in messages:
            if msg["role"] == "system" and isinstance(msg["content"], str):
                # Check for project directory patterns
                for pattern in self.PROJECT_ROOT_PATTERNS:
                    match = re.search(pattern, msg["content"])
                    if match:
                        project_dir = match.group(1)
                        logger.debug(f"Extracted project directory: {project_dir}")
                        self.project_dir = project_dir
                        return project_dir

        # No project directory found in system message
        return None

    def change_to_project_dir(self):
        """Ensure the project directory exists and is a directory before changing to it."""
        expanded_dir = os.path.expanduser(self.project_dir)

        # Check if directory exists
        if not os.path.exists(expanded_dir):
            error = f"Project directory {self.project_dir} does not exist. See https://vmpdocs.a1.lingastic.org/user-guide/?h=project+directory#project-directory-configuration "
            logger.error(error)
            raise Exception(error)

        # Check if it's a directory
        if not os.path.isdir(expanded_dir):
            error_msg = f"Failed to change to project directory {self.project_dir}: Not a directory"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Try to change to the directory
        try:
            os.chdir(expanded_dir)
            logger.info(f"Changed to project directory: {expanded_dir}")
        except PermissionError as e:
            error_msg = f"Failed to change to project directory {self.project_dir}: Permission denied"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to change to project directory {self.project_dir}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    def should_truncate_messages(self, messages):
        """
        Determine if messages should be truncated based on chat context.
        
        In a continuing conversation, we only need the last message from the current request.
        
        Args:
            messages: List of messages to check
            
        Returns:
            bool: True if messages should be truncated, False otherwise
        """
        # If this is a continuing conversation (with existing history)
        # and we have more than 2 messages (system + user), we should truncate
        if self.chat_id and len(messages) > 2:
            return True
        return False
        
    def get_formatted_messages(self, messages):
        """
        Get properly formatted messages for processing.
        
        For continuing conversations, this will truncate to just the last message.
        For new conversations, it will return all messages.
        
        Args:
            messages: List of messages to format
            
        Returns:
            list: Properly formatted messages for processing
        """
        if self.should_truncate_messages(messages):
            # Only keep the last message for continuing conversations
            return [messages[-1]]
        return messages
        
    def update_messages(self, new_messages):
        """
        Update the chat's message history.
        
        Args:
            new_messages: New messages to add to history
        """
        self.messages = new_messages
