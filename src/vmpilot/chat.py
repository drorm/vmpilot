"""
Chat management for VMPilot.
Handles chat IDs, project directories, and session management.
"""

import logging
import secrets
import string
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from . import config
from . import env

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
        self.project_dir = ""
        self.messages = messages or []
        self.output_callback = output_callback

        # Extract project directory from messages if provided
        if system_prompt_suffix:
            logger.debug(f"Using system prompt suffix: {system_prompt_suffix}")
            extracted_dir = env.extract_project_dir(system_prompt_suffix)
            if extracted_dir:
                self.project_dir = extracted_dir
                logger.info(
                    f"Using project directory from messages: {self.project_dir}"
                )

        # Get or generate chat_id
        self.chat_id = self._determine_chat_id(self.messages, output_callback)

        # For tests: change directory now during initialization
        # This matches the behavior expected by the tests
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

    def _determine_chat_id(
        self,
        messages: Optional[List[Dict[str, str]]],
        output_callback: Optional[Callable[[Dict], None]],
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
            return extracted_id

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

    # Compatibility methods for tests
    def extract_project_dir(self, system_prompt_suffix: str = None) -> Optional[str]:
        """
        Extract project directory from system message if present.
        This is a compatibility method for tests - actual implementation is in env.py.

        Args:
            system_prompt_suffix: Optional system prompt suffix to extract project directory from

        Returns:
            Project directory if found, None otherwise
        """
        extracted = env.extract_project_dir(messages)
        if extracted:
            self.project_dir = extracted
        return extracted

    def change_to_project_dir(self):
        """
        Ensure the project directory exists and is a directory before changing to it.
        This is a compatibility method for tests - actual implementation is in env.py.

        Direct implementation for tests - doesn't use env.py to ensure test compatibility
        """
        import os

        # Use the project_dir that was set in __init__
        expanded_dir = os.path.expanduser(self.project_dir)
        logger.debug(
            f"Changing to project directory: {expanded_dir} (original: {self.project_dir})"
        )

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

            # For tests, update env variable
            os.environ["PROJECT_ROOT"] = expanded_dir
        except PermissionError:
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
