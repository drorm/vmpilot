#!/usr/bin/env python3
"""
Patch for worker_llm module.

This script patches the worker_llm module to use environment variables directly
for API keys instead of relying on config.get_api_key.
"""

import os
import sys
from pathlib import Path
import types

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the original worker_llm module
import vmpilot.worker_llm as worker_llm
from vmpilot.config import Provider


# Create a new get_worker_llm function that uses environment variables directly
def patched_get_worker_llm(
    model="claude-3-7-sonnet-latest",
    provider=Provider.ANTHROPIC,
    temperature=worker_llm.TEMPERATURE,
    max_tokens=worker_llm.MAX_TOKENS,
):
    """Patched version of get_worker_llm that uses environment variables directly."""
    if provider == Provider.OPENAI:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key and os.path.exists(os.path.expanduser("~/.openai")):
            with open(os.path.expanduser("~/.openai"), "r") as f:
                api_key = f.read().strip()

        return worker_llm.ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )
    elif provider == Provider.ANTHROPIC:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key and os.path.exists(os.path.expanduser("~/.anthropic/api_key")):
            with open(os.path.expanduser("~/.anthropic/api_key"), "r") as f:
                api_key = f.read().strip()

        return worker_llm.ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


# Replace the original get_worker_llm function with our patched version
worker_llm.get_worker_llm = patched_get_worker_llm

print("worker_llm module patched successfully")
