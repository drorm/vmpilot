"""
response.py
Generates responses from the LLM by delegating to the LiteLLM agent implementation.
This module acts as a bridge between vmpilot.py (or pipeline) and the agent logic.
"""

import logging
from typing import Any, Dict, Generator

# This import points to the LiteLLM agent implementation from the MVP.
# As agent.py is refactored (later steps of issue #88), this might change
# to import directly from vmpilot.agent.
from vmpilot.lllm.agent import generate_responses as agent_generate_responses

logger = logging.getLogger(__name__)


def generate_responses(
    body: Dict[str, Any],
    pipeline_self: Any,
    messages: list,
    system_prompt_suffix: str,
    formatted_messages: list,
) -> Generator[str, None, None]:
    """
    Bridge function that delegates to the LiteLLM agent implementation.

    Args:
        body: Request body from the pipeline or caller.
        pipeline_self: Reference to the pipeline object (if applicable).
        messages: List of messages in the conversation history.
        system_prompt_suffix: Additional text to append to the system prompt.
        formatted_messages: Messages formatted for the LLM.

    Yields:
        Response chunks (strings) as they become available from the agent.
    """
    logger.info(
        "response.py: Delegating response generation to LiteLLM agent implementation (vmpilot.lllm.agent)"
    )

    # Delegate to the LiteLLM agent's response generation logic
    yield from agent_generate_responses(
        body, pipeline_self, messages, system_prompt_suffix, formatted_messages
    )
