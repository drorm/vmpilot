import logging
from typing import Any, Dict

from vmpilot.config import MAX_TOKENS, TEMPERATURE
from vmpilot.config import Provider as APIProvider
from vmpilot.config import config, current_provider
from vmpilot.prompt import get_system_prompt

logger = logging.getLogger(__name__)

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"


def build_litellm_config(
    model: str,
    api_key: str,
    provider: APIProvider,
    system_prompt_suffix: str = "",
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> Dict[str, Any]:
    """
    Build configuration for LiteLLM agent. Handles Anthropic caching and model-specific logic.
    Returns a dict to be passed to lllm/agent.py agent loop.
    """
    enable_prompt_caching = False
    betas = [COMPUTER_USE_BETA_FLAG]

    if provider == APIProvider.ANTHROPIC:
        enable_prompt_caching = True

    if enable_prompt_caching:
        betas.append(PROMPT_CACHING_BETA_FLAG)

    system_prompt = get_system_prompt()
    if system_prompt_suffix:
        system_prompt += f"\n\n{system_prompt_suffix}"

    # Anthropic: add cache_control to system prompt (only for LiteLLM Anthropic)
    if provider == APIProvider.ANTHROPIC:
        provider_config = config.get_provider_config(APIProvider.ANTHROPIC)
        if provider_config.beta_flags:
            betas.extend([flag for flag in provider_config.beta_flags.keys()])
        system_content = {
            "type": "text",
            "text": system_prompt,
        }
        if enable_prompt_caching:
            system_content["cache_control"] = {"type": "ephemeral"}
        extra_headers = {"anthropic-beta": ",".join(betas)}
        return {
            "model": model,
            "api_key": api_key,
            "provider": provider,
            "system_prompt": system_prompt,
            "anthropic_system_content": [
                system_content
            ],  # Wrap in list for Anthropic API
            "anthropic_extra_headers": extra_headers,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    # OpenAI: special handling for o4-mini
    elif provider == APIProvider.OPENAI:
        model_temperature = 1 if model == "o4-mini" else temperature
        return {
            "model": model,
            "api_key": api_key,
            "provider": provider,
            "system_prompt": system_prompt,
            "temperature": model_temperature,
            "max_tokens": max_tokens,
        }

    # Google: no special settings yet
    elif provider == APIProvider.GOOGLE:
        return {
            "model": model,
            "api_key": api_key,
            "provider": provider,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    # Default fallback
    return {
        "model": model,
        "api_key": api_key,
        "provider": provider,
        "system_prompt": system_prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def modify_state_messages(messages):
    """
    For Anthropic: Add cache_control to last 3 messages (LiteLLM format, not LangChain objects).
    This function modifies messages in place for cache control in Anthropic.
    """
    provider = current_provider.get()
    if provider is None or provider != APIProvider.ANTHROPIC:
        return messages

    # Only apply caching if prompt caching is enabled
    provider_config = config.get_provider_config(APIProvider.ANTHROPIC)
    if not (
        provider_config
        and provider_config.beta_flags
        and PROMPT_CACHING_BETA_FLAG in provider_config.beta_flags
    ):
        return messages

    cached = 3
    messages_to_cache = messages[-cached:] if len(messages) >= cached else messages

    for message in reversed(messages_to_cache):
        if cached > 0:
            # Handle different content formats
            content = message.get("content")
            if isinstance(content, list):
                # Content is a list of content blocks
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        block["cache_control"] = {"type": "ephemeral"}
                        cached -= 1
                        break  # Only cache one block per message
            elif isinstance(content, str):
                # Convert string content to structured format for caching
                message["content"] = [
                    {
                        "type": "text",
                        "text": content,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
                cached -= 1
            else:
                # Fallback: add cache_control directly to message
                message["cache_control"] = {"type": "ephemeral"}
                cached -= 1
        else:
            # Remove cache control from older messages
            content = message.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and "cache_control" in block:
                        block.pop("cache_control", None)
            else:
                message.pop("cache_control", None)

    logger.debug(
        f"[LiteLLM] Modified {len(messages_to_cache)} messages for Anthropic cache control"
    )
    return messages


# For API symmetry with agent.py
async def create_agent(
    model: str,
    api_key: str,
    provider: APIProvider,
    system_prompt_suffix: str = "",
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
):
    """
    Returns a config dict for LiteLLM agent loop (used by lllm/agent.py)
    """
    return build_litellm_config(
        model,
        api_key,
        provider,
        system_prompt_suffix,
        temperature,
        max_tokens,
    )
