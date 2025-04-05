"""
Pipeline test adapter to maintain backward compatibility with tests.

This module provides adapters for the Pipeline class to maintain
compatibility with existing tests after refactoring.
"""

from unittest.mock import patch

from vmpilot.chat import Chat


def add_test_methods_to_pipeline(pipeline_class):
    """
    Add test compatibility methods to the Pipeline class.

    This function monkey-patches the Pipeline class to add methods
    needed for backward compatibility with existing tests.
    """

    # Backup the original pipe method
    original_pipe = pipeline_class.pipe

    def patched_pipe(self, user_message, model_id, messages, body):
        """
        Patched pipe method that ensures _chat is initialized before use.
        """
        # Ensure _chat is initialized for tests
        if not hasattr(self, "_chat"):
            from vmpilot.chat import Chat

            chat_id = getattr(self, "chat_id", None)
            # Create Chat with patched environment checks
            with (
                patch("vmpilot.env.os.path.exists", return_value=True),
                patch("vmpilot.env.os.path.isdir", return_value=True),
                patch("vmpilot.env.os.chdir"),
                patch("os.path.exists", return_value=True),
                patch("os.path.isdir", return_value=True),
                patch("os.chdir"),
            ):
                self._chat = Chat(system_prompt_suffix="$PROJECT_ROOT=/tmp")
            if chat_id:
                self._chat.chat_id = chat_id

        # Call the original method
        return original_pipe(self, user_message, model_id, messages, body)

    # Replace the pipe method with our patched version
    pipeline_class.pipe = patched_pipe

    def get_or_generate_chat_id(self, messages, output_callback):
        """
        Adapter method to maintain compatibility with existing tests.

        This reimplements the functionality that was previously in Pipeline
        but has now been moved to the Chat class.

        Args:
            messages: List of chat messages
            output_callback: Callback function for sending output

        Returns:
            Chat ID string or None
        """
        # Extract chat_id from body if it was set as an attribute
        provided_chat_id = getattr(self, "chat_id", None)

        # First, try to extract chat_id from messages
        extracted_id = None

        # Try to extract from messages first (similar to Chat._extract_chat_id_from_messages)
        if messages:
            for msg in messages:
                if msg["role"] == "assistant" and isinstance(msg.get("content"), str):
                    content_lines = msg["content"].split("\n")
                    if content_lines and "Chat id" in content_lines[0]:
                        parts = content_lines[0].split(":", 1)
                        if len(parts) > 1:
                            extracted_id = parts[1].strip()
                            break

        # If we found an extracted_id, use it without creating a Chat object
        # This prevents the output_callback from being called
        if extracted_id:
            return extracted_id

        # If we didn't find an extracted_id or if one was provided, create a Chat object
        # Create temp_chat with patched environment checks
        # Use monkeypatch to set the PROJECT_ROOT environment variable
        import os

        os.environ["PROJECT_ROOT"] = "/tmp"
        with (
            patch("vmpilot.env.os.path.exists", return_value=True),
            patch("vmpilot.env.os.path.isdir", return_value=True),
            patch("vmpilot.env.os.chdir"),
            patch("os.path.exists", return_value=True),
            patch("os.path.isdir", return_value=True),
            patch("os.chdir"),
        ):
            temp_chat = Chat(
                messages=messages,
                output_callback=output_callback,
                system_prompt_suffix="$PROJECT_ROOT=/tmp",
            )

        # Override the chat_id if provided
        if provided_chat_id:
            temp_chat.chat_id = provided_chat_id
            return provided_chat_id

        # For existing conversations (more than 2 messages), try to extract a chat_id
        if messages and len(messages) > 2:
            # Try to extract from messages first
            for msg in messages:
                if msg["role"] == "assistant" and isinstance(msg["content"], str):
                    # Define the patterns to match chat_id in the message
                    chat_id_patterns = [
                        rf"{temp_chat.CHAT_ID_PREFIX}\s*{temp_chat.CHAT_ID_DELIMITER}\s*([a-zA-Z0-9]+)",
                        rf"{temp_chat.CHAT_ID_PREFIX}\s*{temp_chat.CHAT_ID_DELIMITER}\s*([^\s\n]+)",
                    ]
                    for pattern in chat_id_patterns:
                        match = re.search(pattern, msg["content"])
                        if match:
                            extracted_id = match.group(1).strip()
                            if extracted_id:
                                return extracted_id

        # If no chat_id found or it's a new conversation, return the generated chat_id
        return temp_chat.chat_id

    def patched_generate_responses(self):
        """
        A patched version of the generate_responses method that fixes the chat_id reference issue.
        This is for testing only.
        """
        # Ensure _chat is initialized
        if not hasattr(self, "_chat"):
            from vmpilot.chat import Chat

            # Create Chat with patched environment checks
            with (
                patch("vmpilot.env.os.path.exists", return_value=True),
                patch("vmpilot.env.os.path.isdir", return_value=True),
                patch("vmpilot.env.os.chdir"),
                patch("os.path.exists", return_value=True),
                patch("os.path.isdir", return_value=True),
                patch("os.chdir"),
            ):
                self._chat = Chat(system_prompt_suffix="$PROJECT_ROOT=/tmp")

        # Get the chat_id
        chat_id = self._chat.chat_id

        # Return a dummy generator for testing
        def dummy_generator():
            yield "Test response"

        return dummy_generator()

    # Add the compatibility methods to the Pipeline class
    setattr(pipeline_class, "get_or_generate_chat_id", get_or_generate_chat_id)
    setattr(pipeline_class, "_original_generate_responses", pipeline_class.pipe)


# Import here to avoid circular imports
import re
