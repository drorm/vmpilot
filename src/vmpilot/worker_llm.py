"""
Worker LLM module for general-purpose LLM tasks.

This module provides functionality to run tasks on worker LLMs, either synchronously
or asynchronously. It supports different providers and models, making it a flexible
solution for various LLM-based tasks.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from vmpilot.config import MAX_TOKENS, TEMPERATURE
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config

logger = logging.getLogger(__name__)


def get_worker_llm(
    model: str = "claude-3-7-sonnet-latest",
    provider: APIProvider = APIProvider.ANTHROPIC,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> BaseChatModel:
    """Get a worker LLM instance.

    Args:
        model: Model name to use.
        provider: API provider to use.
        temperature: Temperature setting for the LLM.
        max_tokens: Maximum tokens for the LLM response.

    Returns:
        LLM instance based on the specified provider.
    """
    if provider == APIProvider.OPENAI:
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=config.get_api_key(provider),
        )
    elif provider == APIProvider.ANTHROPIC:
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=config.get_api_key(provider),
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def run_worker(
    prompt: str,
    system_prompt: str = "",
    model: str = "claude-3-7-sonnet-latest",
    provider: APIProvider = APIProvider.ANTHROPIC,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """Run a worker LLM task synchronously.

    Args:
        prompt: The prompt to send to the LLM.
        system_prompt: Optional system prompt to set context.
        model: Model name to use.
        provider: API provider to use.
        temperature: Temperature setting for the LLM.
        max_tokens: Maximum tokens for the LLM response.

    Returns:
        The LLM's response as a string.
    """
    logger.debug(f"Running worker LLM task with model {model}")

    # Create messages for the LLM
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    # Get worker LLM
    llm = get_worker_llm(
        model=model, provider=provider, temperature=temperature, max_tokens=max_tokens
    )

    # Generate response
    response = llm.invoke(messages)
    result = response.content.strip()

    logger.debug(f"Worker LLM task completed, response length: {len(result)}")
    return result


async def run_worker_async(
    prompt: str,
    system_prompt: str = "",
    model: str = "claude-3-7-sonnet-latest",
    provider: APIProvider = APIProvider.ANTHROPIC,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """Run a worker LLM task asynchronously.

    Args:
        prompt: The prompt to send to the LLM.
        system_prompt: Optional system prompt to set context.
        model: Model name to use.
        provider: API provider to use.
        temperature: Temperature setting for the LLM.
        max_tokens: Maximum tokens for the LLM response.

    Returns:
        The LLM's response as a string.
    """
    logger.debug(f"Running async worker LLM task with model {model}")

    # Create messages for the LLM
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    # Get worker LLM
    llm = get_worker_llm(
        model=model, provider=provider, temperature=temperature, max_tokens=max_tokens
    )

    # Generate response asynchronously
    response = await llm.ainvoke(messages)
    result = response.content.strip()

    logger.debug(f"Async worker LLM task completed, response length: {len(result)}")
    return result
