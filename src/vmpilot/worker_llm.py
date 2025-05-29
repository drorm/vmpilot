"""
Worker LLM module for general-purpose LLM tasks.

This module provides functionality to run tasks on worker LLMs, either synchronously
or asynchronously. It supports different providers and models, making it a flexible
solution for various LLM-based tasks.
"""

import logging

from vmpilot.config import MAX_TOKENS, TEMPERATURE
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config

# from pydantic import SecretStr


logger = logging.getLogger(__name__)


def get_worker_llm(
    model: str = "claude-3-7-sonnet-latest",
    provider: APIProvider = APIProvider.ANTHROPIC,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
):
    """Get a worker LLM instance.

    Args:
        model: Model name to use.
        provider: API provider to use.
        temperature: Temperature setting for the LLM.
        max_tokens: Maximum tokens for the LLM response.

    Returns:
        LLM instance based on the specified provider.
    """
    # This function is obsolete in LiteLLM context -- kept for backward compatibility.
    # Just call run_worker or run_worker_async.
    raise NotImplementedError(
        "get_worker_llm is not used in LiteLLM-based implementation. Use run_worker/run_worker_async instead."
    )


def run_worker(
    prompt: str,
    system_prompt: str = "",
    model: str = "claude-3-7-sonnet-latest",
    provider: APIProvider = APIProvider.ANTHROPIC,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """Run a worker LLM task synchronously using LiteLLM.

    Args:
        prompt: The prompt to send to the LLM.
        system_prompt: Optional system prompt to set context.
        model: Model name to use (LiteLLM model string).
        provider: API provider (used to fetch API key from config).
        temperature: Temperature setting for the LLM.
        max_tokens: Maximum tokens for the LLM response.

    Returns:
        The LLM's response as a string.
    """
    logger.debug(f"Running worker LLM task with model {model} via LiteLLM")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    api_key = config.get_api_key(provider)
    # LiteLLM uses `engine` for Azure deployments, passed via `model` parameter like `azure/<your-deployment-name>`
    # For other providers, `model` is usually sufficient.
    # Provider-specific parameters might be needed for `litellm.completion` if not covered by env vars.

    try:
        import litellm

        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,  # LiteLLM uses max_tokens
            api_key=api_key,
            # Add other provider-specific params if needed, e.g., api_base for custom OpenAI endpoints
            # For Azure, ensure AZURE_API_KEY, AZURE_API_BASE, AZURE_API_VERSION are set or passed if model starts with "azure/"
        )
        # LiteLLM response structure: response.choices[0].message.content
        content = getattr(
            getattr(getattr(response, "choices", [{}])[0], "message", None),
            "content",
            None,
        )
        result = content.strip() if content else ""
    except Exception as e:
        logger.error(f"Error during LiteLLM call in run_worker: {e}")
        # Log more details if available from LiteLLM exception types
        if hasattr(e, "status_code"):
            logger.error(
                f"LiteLLM API Error - Status: {getattr(e, 'status_code', 'unknown')}, Message: {getattr(e, 'message', str(e))}"
            )
        raise

    logger.debug(f"Worker LLM task completed, response length: {len(result)}")
    return result


async def run_worker_async(
    prompt: str,
    system_prompt: str = "",
    model: str = "claude-3-sonnet-20240229",  # Updated to a common LiteLLM model identifier
    provider: APIProvider = APIProvider.ANTHROPIC,  # Provider can still be used for config lookups
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """Run a worker LLM task asynchronously using LiteLLM.

    Args:
        prompt: The prompt to send to the LLM.
        system_prompt: Optional system prompt to set context.
        model: Model name to use (LiteLLM model string).
        provider: API provider (used to fetch API key from config).
        temperature: Temperature setting for the LLM.
        max_tokens: Maximum tokens for the LLM response.

    Returns:
        The LLM's response as a string.
    """
    logger.debug(f"Running async worker LLM task with model {model} via LiteLLM")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    api_key = config.get_api_key(provider)
    # LiteLLM uses `engine` for Azure deployments, passed via `model` parameter like `azure/<your-deployment-name>`
    # For other providers, `model` is usually sufficient.

    try:
        import litellm

        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,  # LiteLLM uses max_tokens
            api_key=api_key,
            # Add other provider-specific params if needed
        )
        # LiteLLM response structure: response.choices[0].message.content
        content = getattr(
            getattr(getattr(response, "choices", [{}])[0], "message", None),
            "content",
            None,
        )
        result = content.strip() if content else ""
    except Exception as e:
        logger.error(f"Error during LiteLLM async call in run_worker_async: {e}")
        if hasattr(e, "status_code"):
            logger.error(
                f"LiteLLM API Error - Status: {getattr(e, 'status_code', 'unknown')}, Message: {getattr(e, 'message', str(e))}"
            )
        raise

    logger.debug(f"Async worker LLM task completed, response length: {len(result)}")
    return result
