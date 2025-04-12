"""
Chat management for VMPilot.
Handles chat IDs, project directories, and session management.
"""

import logging
import os
import secrets
import string
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from . import config, env
from .project import Project

logger = logging.getLogger(__name__)


class Chat:
    """
    Class to manage chat sessions, including IDs and project directories.
    """

    CHAT_ID_PREFIX = "Chat id"
    CHAT_ID_DELIMITER = ":"

    def __init__(
        self,
        messages=None,
        output_callback=None,
        system_prompt_suffix=None,
    ):
        """
        Initialize a chat session.

        Args:
            messages: Optional list of chat messages to extract information from.
            output_callback: Optional callback function for sending output.
        """
        # Set initial project directory value
        self.messages = messages or []
        self.output_callback = output_callback
        self.new_chat = False
        self.done = False
        # Get or generate chat_id
        self.chat_id = self._determine_chat_id(self.messages, output_callback)

        # Check project setup
        project = Project(system_prompt_suffix, self.output_callback)

        if self.new_chat:
            project.check_project_structure()
            if project.done():
                # If it's a new project and the check sends a message to the user, no need to continue
                self.done = True
                return

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

    def _determine_chat_id(
        self,
        messages: Optional[List[Dict[str, str]]],
        output_callback: Callable[[Dict], None],
    ) -> str:
        """
        Extract an existing chat_id if present, or generate a new one if needed.

        Args:
            messages: List of chat messages
            output_callback: Callback function for sending output

        Returns:
            Chat ID string
        """
        # Try to extract an existing chat_id from messages
        extracted_id = self._extract_chat_id_from_messages(messages)
        if extracted_id:
            self.new_chat = False
            return extracted_id

        self.new_chat = True
        # If no existing chat_id found, generate a new one
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

    def _extract_chat_id_from_messages(
        self, messages: Optional[List[Dict[str, str]]]
    ) -> Optional[str]:
        """
        Extract chat_id from messages if present.

        Args:
            messages: List of chat messages

        Returns:
            Extracted chat_id or None if not found
        """
        if not messages:
            return None

        # Check all messages for chat_id, prioritizing the most recent ones
        for msg in messages:
            logger.debug(
                f"Checking message content: {msg.get('content')} isinstance: {isinstance(msg.get('content'), str)}"
            )

            if msg["role"] == "assistant":
                content = msg.get("content", "")
                if isinstance(content, list) and len(content) > 0:
                    for content_item in content:
                        if (
                            isinstance(content_item, dict)
                            and content_item.get("type") == "text"
                        ):
                            text = content_item.get("text", "")
                            if text:
                                content_lines = text.split("\n")
                                if content_lines and content_lines[0].startswith(
                                    self.CHAT_ID_PREFIX
                                ):
                                    # Extract chat_id from the first line
                                    parts = content_lines[0].split(
                                        self.CHAT_ID_DELIMITER, 1
                                    )
                                    if len(parts) > 1:
                                        extracted_id = parts[1].strip()
                                        return extracted_id

        # If we reach here, no chat_id was found
        logger.debug("No chat_id found in messages")
        return None

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
