"""
LiteLLM Migration MVP Implementation for VMPilot.
Provides a simple agent loop with shell tool support using LiteLLM.
"""

# Version information
__version__ = "0.1.0"

# Core functionality
from vmpilot.lllm.agent import agent_loop, parse_tool_calls
from vmpilot.tools.shelltool import execute_shell_command as execute_tool
from vmpilot.tools.shelltool import shell_tool

__all__ = [
    # Agent functionality
    "agent_loop",
    "parse_tool_calls",
    # Tools
    "shell_tool",
    "execute_shell_tool",
    "execute_tool",
]
