"""
LiteLLM Migration MVP Implementation for VMPilot.
Provides a simple agent loop with shell tool support using LiteLLM.
"""

from vmpilot.lllm.agent import agent_loop, generate_responses, parse_tool_calls
from vmpilot.lllm.cli import main
from vmpilot.lllm.shelltool import SHELL_TOOL, execute_shell_tool, execute_tool

__all__ = [
    "agent_loop",
    "generate_responses",
    "parse_tool_calls",
    "main",
    "SHELL_TOOL",
    "execute_shell_tool",
    "execute_tool",
]
