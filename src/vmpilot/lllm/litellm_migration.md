# LiteLLM Migration

This document describes the integration of LiteLLM into VMPilot as an alternative to the LangChain-based implementation.

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

## Integration with VMPilot

The LiteLLM implementation is integrated with VMPilot through a feature flag system. When the `VMPILOT_USE_LITELLM` environment variable is set to `true`, VMPilot will use the LiteLLM-based agent instead of the LangChain-based agent.

### Feature Flag Implementation

The implementation uses a simple feature flag in `vmpilot.py` to determine which implementation to use:

```python
# Check if we should use the LiteLLM implementation
try:
    from vmpilot.lllm import use_litellm
    use_lllm = use_litellm()
except ImportError:
    use_lllm = False
    
if use_lllm:
    from vmpilot.lllm import generate_responses
    logger.info("Using LiteLLM implementation")
else:
    from vmpilot.response import generate_responses
    logger.info("Using LangChain implementation")
```

This approach allows for a gradual migration and easy rollback if needed.

## Usage

### Environment Variables

- `VMPILOT_USE_LITELLM`: Set to `true`, `1`, or `yes` to enable the LiteLLM implementation
- `VMPILOT_LITELLM_MODEL`: The model to use with LiteLLM (default: `gpt-4o`)

### Running with LiteLLM

You can use the provided script to run VMPilot with the LiteLLM implementation:

```bash
./scripts/run_with_litellm.sh "your command here"
```

Or set the environment variables manually:

```bash
export VMPILOT_USE_LITELLM=true
export VMPILOT_LITELLM_MODEL="anthropic/claude-3-sonnet"  # Optional
python -m vmpilot.cli "your command here"
```

### Testing the Integration

To test the integration with the VMPilot pipeline:

```bash
./scripts/test_litellm_integration.sh
```

## Implementation Details

The LiteLLM implementation is located in the `src/vmpilot/lllm` directory and consists of:

- `agent.py`: Core agent implementation
  - `agent_loop`: The main loop that processes user input, sends it to the LLM, executes tools, and returns the final response
  - `generate_responses`: Integration with the VMPilot pipeline, compatible with the original implementation
  - `parse_tool_calls`: Helper function to extract tool calls from LLM responses

- `shelltool.py`: Shell tool implementation
  - `SHELL_TOOL`: Tool definition for the shell tool
  - `execute_shell_tool`: Function to execute shell commands

- `cli.py`: Standalone CLI for direct interaction with the LiteLLM agent

- `config.py`: Configuration utilities
  - `use_litellm`: Function to check if the LiteLLM implementation should be used
  - `get_default_model`: Function to get the default model to use with LiteLLM

- `test_integration.py`: Test script for verifying the integration with the VMPilot pipeline

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

## Current Limitations

1. Only the shell tool is currently implemented
2. No streaming support for individual tokens (only for complete messages)
3. Limited error handling compared to the LangChain implementation
4. No memory management for conversation history
5. No support for parallel tool execution

## Future Improvements

1. Add support for more tools
   - File editing tools
   - Google search tools
   - GitHub integration tools

2. Implement streaming responses for individual tokens
   - Enhance UX with real-time token streaming

3. Add memory management for conversation history
   - Support for persistent conversations
   - Context-aware responses across multiple interactions

4. Support for more LLM providers
   - Add support for local models
   - Add support for Azure OpenAI

5. Better error handling and recovery
   - Graceful degradation on API errors
   - Retry mechanisms for transient failures

6. Performance optimizations
   - Parallel tool execution
   - Caching for repeated queries
