# VMPilot LiteLLM Migration MVP

This directory contains an MVP implementation of VMPilot using LiteLLM instead of LangChain.

## Overview

The LiteLLM implementation provides a simpler, more direct approach to interacting with LLMs, with fewer dependencies and a more straightforward codebase. This implementation is designed to be a drop-in replacement for the LangChain-based implementation, with minimal changes to the existing codebase.

## Components

- `agent.py`: Contains the core agent implementation, including:
  - `agent_loop`: The main loop that processes user input, sends it to the LLM, executes tools, and returns the final response
  - `generate_responses`: Integration with the VMPilot pipeline, compatible with the original implementation
  - `parse_tool_calls`: Helper function to extract tool calls from LLM responses

- `shelltool.py`: Contains the shell tool implementation for executing shell commands

- `cli.py`: Command-line interface for direct interaction with the LiteLLM agent

- `config.py`: Configuration utilities for the LiteLLM implementation

- `test_integration.py`: Test script for verifying the integration with the VMPilot pipeline

## Integration with VMPilot

The LiteLLM implementation is integrated with VMPilot through a feature flag system. When the `VMPILOT_USE_LITELLM` environment variable is set to `true`, VMPilot will use the LiteLLM-based agent instead of the LangChain-based agent.

```bash
# Enable LiteLLM implementation
export VMPILOT_USE_LITELLM=true

# Optionally specify a model
export VMPILOT_LITELLM_MODEL="anthropic/claude-3-sonnet"

# Run VMPilot with LiteLLM
python -m vmpilot.cli "your command here"
```

You can also use the provided scripts:

```bash
# Run VMPilot with LiteLLM
./scripts/run_with_litellm.sh "your command here"

# Test the LiteLLM integration
./scripts/test_litellm_integration.sh
```

## Usage

### Standalone CLI

You can use the LiteLLM implementation directly without going through the VMPilot pipeline:

```bash
# Run a command using the LiteLLM agent
python -m vmpilot.lllm.cli "your command here"

# Specify a different model
python -m vmpilot.lllm.cli --model "anthropic/claude-3-sonnet" "your command here"
```

### Integration Testing

To test the integration with the VMPilot pipeline:

```bash
# Test the integration with the VMPilot pipeline
python -m vmpilot.lllm.test_integration "your command here"
```

### Supported Models

The LiteLLM implementation supports the following models:

- OpenAI models (e.g., `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`)
- Anthropic models (e.g., `anthropic/claude-3-sonnet`, `anthropic/claude-3-opus`)
- Google models (e.g., `google/gemini-pro`, `google/gemini-1.5-pro`)

## Future Improvements

1. Add support for more tools (currently only shell tool is implemented)
2. Implement streaming responses for individual tokens (currently only supports streaming complete messages)
3. Add memory management for conversation history
4. Better error handling and recovery
5. Support for more advanced features like parallel tool execution
