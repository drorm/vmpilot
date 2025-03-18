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
        self, chat_id: Optional[str] = None, project_dir: Optional[str] = None
    ):
        """
        Initialize a chat session.

        Args:
            chat_id: Optional chat ID. If not provided, one will be generated.
            project_dir: Optional project directory. If not provided, will use default_project.
        """
        self.chat_id = chat_id or self._generate_chat_id()
        self.project_dir = project_dir or config.DEFAULT_PROJECT
        self._ensure_project_dir_exists()

    def _generate_chat_id(self) -> str:
        """Generate a new random chat ID."""
        return "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(8)
        )

    def _ensure_project_dir_exists(self):
        """Ensure the project directory exists, creating it if necessary."""
        project_path = Path(os.path.expanduser(self.project_dir))
        if not project_path.exists():
            logger.warning(f"Project directory {self.project_dir} does not exist")
            # We don't create it as it might be a typo or misconfiguration

    def initialize_chat(
        self, messages: List[Dict[str, str]], output_callback: Callable[[Dict], None]
    ) -> str:
        """
        Initialize the chat session - extract project directory, get/generate chat ID,
        and change to project directory if needed.

        Args:
            messages: List of chat messages
            output_callback: Callback function for sending output

        Returns:
            Chat ID string
        """
        # Extract project directory from system message if present
        self.extract_project_dir(messages)

        # Get or generate chat ID
        chat_id = self._get_or_generate_chat_id(messages, output_callback)

        # Change to project directory for new chats
        if len(messages) <= 2:  # only system and one user message
            self.change_to_project_dir()
            # Note: logging is done inside change_to_project_dir

        logger.info(f"Using chat_id: {chat_id}")
        return chat_id

    def _get_or_generate_chat_id(
        self, messages: List[Dict[str, str]], output_callback: Callable[[Dict], None]
    ) -> str:
        """
        Get an existing chat_id from messages or use/generate one.

        Args:
            messages: List of chat messages
            output_callback: Callback function for sending output

        Returns:
            Chat ID string
        """
        # If we already have a chat_id, use it
        if self.chat_id:
            return self.chat_id

        # Check if this is a new chat (only system and one user message)
        if len(messages) <= 2:
            # New chat, generate and announce chat ID
            output_callback(
                {
                    "type": "text",
                    "text": f"{self.CHAT_ID_PREFIX} {self.CHAT_ID_DELIMITER}{self.chat_id}\n\n",
                }
            )
            logger.debug(f"Generated new chat_id: {self.chat_id}")
            return self.chat_id
        else:
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
                            self.chat_id = parts[1].strip()
                            logger.debug(f"Extracted chat_id: {self.chat_id}")
                            return self.chat_id

            # If we couldn't find a chat_id, use the one we have
            logger.warning(
                "Could not extract chat_id from messages, using generated one"
            )
            return self.chat_id

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
                        logger.info(f"Extracted project directory: {project_dir}")
                        self.project_dir = project_dir
                        self._ensure_project_dir_exists()
                        return project_dir

        # No project directory found in system message
        return None

    def change_to_project_dir(self):
        """Change to the project directory."""
        try:
            expanded_dir = os.path.expanduser(self.project_dir)
            os.chdir(expanded_dir)
            logger.info(f"Changed to project directory: {expanded_dir}")
        except Exception as e:
            logger.error(
                f"Failed to change to project directory {self.project_dir}: {e}"
            )
