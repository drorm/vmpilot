"""
LiteLLM Migration MVP Implementation for VMPilot.
Provides a simple agent loop with shell tool support using LiteLLM.
"""

# Version information
__version__ = "0.1.0"

# Core functionality
from vmpilot.lllm.agent import agent_loop, generate_responses, parse_tool_calls
from vmpilot.lllm.cli import main
from vmpilot.lllm.config import get_default_model, use_litellm
from vmpilot.lllm.shelltool import SHELL_TOOL, execute_shell_tool, execute_tool

__all__ = [
    # Agent functionality
    "agent_loop",
    "generate_responses",
    "parse_tool_calls",
    # CLI
    "main",
    # Tools
    "SHELL_TOOL",
    "execute_shell_tool",
    "execute_tool",
    # Configuration
    "use_litellm",
    "get_default_model",
]
