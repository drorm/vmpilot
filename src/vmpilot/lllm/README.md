# VMPilot LiteLLM Migration MVP

This directory contains an MVP implementation of VMPilot using LiteLLM instead of LangChain.

## Overview

The LiteLLM implementation provides a simpler, more direct approach to interacting with LLMs, with fewer dependencies and a more straightforward codebase.

## Components

- `agent.py`: Contains the core agent implementation, including:
  - `agent_loop`: The main loop that processes user input, sends it to the LLM, executes tools, and returns the final response
  - `generate_responses`: Integration with the VMPilot pipeline, compatible with the original implementation
  - `parse_tool_calls`: Helper function to extract tool calls from LLM responses

- `shelltool.py`: Contains the shell tool implementation for executing shell commands

- `cli.py`: Command-line interface for direct interaction with the LiteLLM agent

- `test_integration.py`: Test script for verifying the integration with the VMPilot pipeline

## Usage

### Standalone CLI

```bash
# Run a command using the LiteLLM agent
python -m vmpilot.lllm.cli "your command here"

# Specify a different model
python -m vmpilot.lllm.cli --model "anthropic/claude-3-sonnet" "your command here"
```

### Integration Testing

```bash
# Test the integration with the VMPilot pipeline
python -m vmpilot.lllm.test_integration "your command here"
```

### Pipeline Integration

The `generate_responses` function in `agent.py` is designed to be a drop-in replacement for the original function in `response.py`. It follows the same interface but uses the LiteLLM-based agent loop instead of the LangChain-based process_messages function.

## Future Improvements

1. Add support for more tools (currently only shell tool is implemented)
2. Implement streaming responses for better UX
3. Add memory management for conversation history
4. Support for more LLM providers
5. Better error handling and recovery