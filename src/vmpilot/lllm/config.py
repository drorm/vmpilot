"""
Configuration for the LiteLLM implementation.
"""

import os
from typing import Optional


def use_litellm() -> bool:
    """Check if the LiteLLM implementation should be used."""
    return os.environ.get("VMPILOT_USE_LITELLM", "").lower() in ("true", "1", "yes")


def get_default_model() -> str:
    """Get the default model to use with LiteLLM."""
    return os.environ.get("VMPILOT_LITELLM_MODEL", "gpt-4o")
