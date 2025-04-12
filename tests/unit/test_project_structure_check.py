"""
Test the project structure check behavior to ensure options are only shown once.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from vmpilot.chat import Chat
from vmpilot.project import Project


class TestProjectStructureCheck(unittest.TestCase):
    """Test the project structure check behavior in Chat class."""

    @patch("vmpilot.project.Project.check_vmpilot_structure")
    @patch("vmpilot.chat.Chat._determine_chat_id")  # Patch to avoid chat ID generation
    @patch("vmpilot.chat.Chat.change_to_project_dir")  # Patch to avoid directory checks
    def test_new_chat_missing_structure_shows_options(
        self, mock_change_dir, mock_determine_chat_id, mock_check_structure
    ):
        """Test that a new chat with missing structure shows options."""
        # Setup mocks
        mock_check_structure.return_value = False  # Structure doesn't exist
        mock_determine_chat_id.return_value = "test-chat-id"
        mock_change_dir.return_value = True

        # Create a mock callback that we'll use only for the structure check
        mock_callback = MagicMock()

        # Create a Chat instance with a generic message
        chat = Chat(
            messages=[{"role": "user", "content": "Hello"}],
            output_callback=mock_callback,
        )

        # Reset the mock to clear any calls from initialization
        mock_callback.reset_mock()

        # Manually call the method to test
        result = chat._check_project_structure("/fake/project/dir")

        # Assert that options were shown and method returned False
        self.assertFalse(result)

        # Check that the callback was called with the options message
        self.assertTrue(mock_callback.called)

        # At least one call should contain the options text
        options_call_found = False
        for call in mock_callback.call_args_list:
            if (
                call[0]
                and isinstance(call[0][0], dict)
                and call[0][0].get("type") == "text"
            ):
                text = call[0][0].get("text", "")
                if "Would you like me to:" in text:
                    options_call_found = True
                    break

        self.assertTrue(
            options_call_found, "Options message not found in callback calls"
        )

    @patch("vmpilot.project.Project.check_vmpilot_structure")
    @patch("vmpilot.chat.Chat._determine_chat_id")  # Patch to avoid chat ID generation
    @patch("vmpilot.chat.Chat.change_to_project_dir")  # Patch to avoid directory checks
    def test_user_responding_to_options_proceeds(
        self, mock_change_dir, mock_determine_chat_id, mock_check_structure
    ):
        """Test that when user responds to options, chat proceeds without showing options again."""
        # Setup mocks
        mock_check_structure.return_value = False  # Structure doesn't exist
        mock_determine_chat_id.return_value = "test-chat-id"
        mock_change_dir.return_value = True

        # Create a mock callback
        mock_callback = MagicMock()

        # Test responses for each option
        option_responses = [
            "option c",  # Explicit option selection
            "I choose option b",  # Natural language selection
            "a",  # Single letter selection
            "skip project setup",  # Keyword for option A
            "create standard files",  # Keyword for option B
            "analyze my code",  # Keyword for option C
        ]

        for response in option_responses:
            # Create a Chat instance with a response to the options
            chat = Chat(
                messages=[{"role": "user", "content": response}],
                output_callback=mock_callback,
            )

            # Reset the mock to clear any calls from initialization
            mock_callback.reset_mock()

            # Manually call the method to test
            result = chat._check_project_structure("/fake/project/dir")

            # Assert that the method returned True to proceed with the chat
            self.assertTrue(result, f"Failed with response: '{response}'")

            # Check that no options message was sent
            options_call_found = False
            for call in mock_callback.call_args_list:
                if (
                    call[0]
                    and isinstance(call[0][0], dict)
                    and call[0][0].get("type") == "text"
                ):
                    text = call[0][0].get("text", "")
                    if "Would you like me to:" in text:
                        options_call_found = True
                        break

            self.assertFalse(
                options_call_found, f"Options shown again for response: '{response}'"
            )


if __name__ == "__main__":
    unittest.main()
