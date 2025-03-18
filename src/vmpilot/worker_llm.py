"""
Worker LLM module for specialized LLM tasks.

This module provides functionality to delegate specific tasks to worker LLMs,
such as generating commit messages from Git diffs.
"""

import logging
from typing import Dict, List, Optional, Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from vmpilot.config import MAX_TOKENS, TEMPERATURE
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config

logger = logging.getLogger(__name__)

# System prompt for commit message generation
COMMIT_MESSAGE_SYSTEM_PROMPT = """You are a commit message generator for an AI assistant called VMPilot.
Your task is to analyze Git diffs and generate concise, informative commit messages.

Your commit messages should:
1. Start with a verb in the present tense (e.g., "Add", "Fix", "Update")
2. Be clear and descriptive
3. Focus on the "what" and "why" of the changes
4. Be no longer than 72 characters for the first line
5. Optionally include a more detailed description after a blank line

Example good commit messages:
- "Add user authentication to API endpoints"
- "Fix race condition in background task processing"
- "Refactor database connection handling for better error recovery"

Please analyze the provided Git diff and generate an appropriate commit message.
"""


def get_worker_llm(
    model: str = "gpt-3.5-turbo",
    provider: APIProvider = APIProvider.OPENAI,
    temperature: float = 0.2,
    max_tokens: int = 256,
) -> ChatOpenAI:
    """Get a worker LLM instance.

    Args:
        model: Model name to use.
        provider: API provider to use.
        temperature: Temperature setting for the LLM.
        max_tokens: Maximum tokens for the LLM response.

    Returns:
        ChatOpenAI instance.
    """
    if provider == APIProvider.OPENAI:
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=config.get_api_key(provider),
        )
    else:
        # Add support for other providers as needed
        raise ValueError(f"Unsupported provider: {provider}")


async def generate_commit_message(
    diff: str,
    model: str = "gpt-3.5-turbo",
    provider: APIProvider = APIProvider.OPENAI,
    temperature: float = 0.2,
) -> str:
    """Generate a commit message from a Git diff.

    Args:
        diff: Git diff to analyze.
        model: Model name to use.
        provider: API provider to use.
        temperature: Temperature setting for the LLM.

    Returns:
        Generated commit message.
    """
    logger.debug("Generating commit message from diff")

    # Truncate diff if it's too large
    if len(diff) > 8000:
        logger.warning("Diff is too large, truncating")
        diff = diff[:8000] + "\n...[truncated]..."

    # Create messages for the LLM
    messages = [
        SystemMessage(content=COMMIT_MESSAGE_SYSTEM_PROMPT),
        HumanMessage(
            content=f"Here is the Git diff to analyze:\n\n```diff\n{diff}\n```"
        ),
    ]

    # Get worker LLM
    llm = get_worker_llm(model=model, provider=provider, temperature=temperature)

    # Generate commit message
    response = await llm.ainvoke(messages)
    commit_message = response.content.strip()

    logger.debug(f"Generated commit message: {commit_message}")
    return commit_message
