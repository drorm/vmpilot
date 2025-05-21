# VMPilot LiteLLM Migration

This document describes the complete integration of LiteLLM into VMPilot as a replacement for the LangChain-based implementation.

## Overview

The LiteLLM implementation provides a simpler, more direct approach to interacting with LLMs, with fewer dependencies and a more straightforward codebase. This implementation is designed to be a drop-in replacement for the LangChain-based implementation, with minimal changes to the existing codebase.

## Benefits of LiteLLM

1. **Simplified Architecture**
   - Direct LLM API access without LangChain abstraction layers
   - Closer to provider APIs for better control and debugging

2. **Reduced Dependencies**
   - LiteLLM has fewer dependencies than LangChain
   - Removes dependency on LangGraph and other LangChain components

3. **Unified Provider Interface**
   - LiteLLM provides consistent interface across all LLM providers
   - Simplifies provider switching and model experimentation

4. **Better Maintainability**
   - More straightforward codebase with direct LLM interactions
   - Easier to understand, extend, and debug

## Architecture Comparison

### LangChain-based Implementation

```
User Input → LangChain Agent → LangChain Tools → Output
              ↑                  ↑
              │                  │
              └── LangGraph ────┘
```

### LiteLLM-based Implementation

```
User Input → LiteLLM Agent Loop → Tool Execution → Output
              ↑                    ↑
              │                    │
              └── Direct API ─────┘
```

The LiteLLM implementation removes the LangChain abstraction layer and directly interacts with the LLM API, resulting in a simpler and more maintainable codebase.

## Implementation Details

The LiteLLM implementation is located in the `src/vmpilot/lllm` directory and consists of:

- `agent.py`: Core agent implementation
  - `agent_loop`: The main loop that processes user input, sends it to the LLM, executes tools, and returns the final response
  - `generate_responses`: Integration with the VMPilot pipeline, compatible with the original implementation
  - `parse_tool_calls`: Helper function to extract tool calls from LLM responses

- `shelltool.py`: Shell tool implementation
  - `shell_tool`: Tool definition for the shell tool
  - `execute_shell_tool`: Function to execute shell commands

- `cli.py`: Standalone CLI for direct interaction with the LiteLLM agent

- `config.py`: Configuration utilities
  - `use_litellm`: Function to check if the LiteLLM implementation should be used
  - `get_default_model`: Function to get the default model to use with LiteLLM

- `test_integration.py`: Test script for verifying the integration with the VMPilot pipeline
- `test_shell.py`: Test script for the shell tool implementation

## Integration with VMPilot

The LiteLLM implementation is now the default for VMPilot. The LangChain-based implementation has been deprecated and is no longer supported.

### Changes Made During Integration

1. **Created LiteLLM Implementation**
   - Created a new directory `src/vmpilot/lllm` for the LiteLLM implementation
   - Implemented the core agent loop in `agent.py`
   - Implemented the shell tool in `shelltool.py`
   - Created a standalone CLI in `cli.py`
   - Added configuration utilities in `config.py`

2. **Integration with VMPilot Pipeline**
   - Added a feature flag in `vmpilot.py` to conditionally use the LiteLLM implementation
   - Implemented a `generate_responses` function in `agent.py` that follows the same interface as the original function in `response.py`
   - Ensured compatibility with the existing pipeline by maintaining the same function signature and behavior

3. **Testing and Utilities**
   - Created a test script `test_integration.py` to verify the integration with the VMPilot pipeline
   - Added a shell script `scripts/test_litellm_integration.sh` to test the integration with the VMPilot pipeline

## Usage

### Running VMPilot

```bash
# Run VMPilot (LiteLLM is now the default)
python -m vmpilot.cli "your command here"

# Or using the CLI script
./bin/cli.sh "your command here"

# Optionally specify a model (default is gpt-4o)
export VMPILOT_LITELLM_MODEL="anthropic/claude-3-sonnet"
./bin/cli.sh "your command here"
```

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

# Or use the provided script
./scripts/test_litellm_integration.sh
```

### Supported Models

The LiteLLM implementation supports the following models:

- OpenAI models (e.g., `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`)
- Anthropic models (e.g., `anthropic/claude-3-sonnet`, `anthropic/claude-3-opus`)
- Google models (e.g., `google/gemini-pro`, `google/gemini-1.5-pro`)

## Current Limitations

1. Only the shell tool is currently implemented
2. No streaming support for individual tokens (only for complete messages)
3. Limited error handling compared to the LangChain implementation
4. No memory management for conversation history
5. No support for parallel tool execution

## Future Improvements

1. **Implement More Tools**
   - File editing tools
   - Google search tools
   - GitHub integration tools

2. **Implement Streaming Responses**
   - Enhance UX with real-time token streaming

3. **Add Memory Management**
   - Support for persistent conversations
   - Context-aware responses across multiple interactions

4. **Support for More LLM Providers**
   - Add support for local models
   - Add support for Azure OpenAI

5. **Improve Error Handling**
   - Graceful degradation on API errors
   - Retry mechanisms for transient failures

6. **Performance Optimizations**
   - Parallel tool execution
   - Caching for repeated queries
