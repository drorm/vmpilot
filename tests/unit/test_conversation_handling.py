"""
Unit tests for conversation handling in VMPilot.

These tests verify that the agent can:
1. Handle multiple tools in one request
2. Maintain conversation context across multiple requests
3. Process follow-up questions that reference previous context
"""

import asyncio
import os
import uuid
from typing import Any, Dict, List

import pytest
from pytest import mark

from vmpilot.agent import process_messages
from vmpilot.config import Provider


class TestConversationHandling:
    """Tests for conversation handling capabilities."""

    @pytest.fixture
    def thread_id(self):
        """Generate a unique thread ID for each test."""
        return f"test-conversation-{uuid.uuid4()}"

    @pytest.fixture
    def message_collector(self):
        """Fixture to collect messages from the agent."""
        messages = []

        def collect_message(message: Dict):
            messages.append(message)

        return messages, collect_message

    @pytest.fixture
    def tool_output_collector(self):
        """Fixture to collect tool outputs."""
        outputs = []

        def collect_tool_output(output: Any, name: str):
            outputs.append({"output": output, "name": name})

        return outputs, collect_tool_output

    @pytest.mark.asyncio
    async def test_multi_step_conversation(
        self, thread_id, message_collector, tool_output_collector
    ):
        """
        Test a multi-step conversation where context is preserved between requests.

        This test simulates the conversation:
        1. "show me /home and then the total disk space for the user in there"
        2. "Show me 10 files in that user's dir"
        """
        messages_list, collect_message = message_collector
        tool_outputs, collect_tool_output = tool_output_collector

        # First query
        initial_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "show me /home and then the total disk space for the user in there",
                    }
                ],
            }
        ]

        # Process the first message
        await process_messages(
            model="gpt-4o",
            provider=Provider.OPENAI,
            system_prompt_suffix="",
            messages=initial_messages,
            output_callback=collect_message,
            tool_output_callback=collect_tool_output,
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            thread_id=thread_id,
        )

        # Verify tool execution for the first message
        tool_names = [tool["name"] for tool in tool_outputs]
        assert "shell" in tool_names, "Shell tool should have been used"

        # Look for directory listing or disk usage commands
        tool_outputs_text = str(tool_outputs)
        # The LLM may choose to use either ls or du commands to fulfill the request
        assert any(
            cmd in tool_outputs_text for cmd in ["ls", "du"]
        ), "Should have executed directory listing or disk usage command"

        # Clear tool outputs for the next test
        tool_outputs.clear()

        # Follow-up query
        followup_messages = initial_messages + [
            # Add the AI's response from the first query
            {"role": "assistant", "content": [messages_list[-1]]},
            # Add the follow-up query
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Show me 10 files in that user's dir"}
                ],
            },
        ]

        # Process the follow-up message
        await process_messages(
            model="gpt-4o",
            provider=Provider.OPENAI,
            system_prompt_suffix="",
            messages=followup_messages,
            output_callback=collect_message,
            tool_output_callback=collect_tool_output,
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            thread_id=thread_id,
        )

        # Verify tool execution for the follow-up message
        tool_names = [tool["name"] for tool in tool_outputs]
        assert "shell" in tool_names, "Shell tool should have been used in follow-up"

        # Verify the follow-up used context from the first query
        tool_outputs_text = str(tool_outputs)
        assert (
            "/home/dror" in tool_outputs_text
        ), "Should reference user directory from context"

        # Either ls or find should be used to list files
        assert any(
            cmd in tool_outputs_text for cmd in ["ls", "find"]
        ), "Should use ls or find to list files"
