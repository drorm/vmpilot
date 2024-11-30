# Compute Pipeline

> [!CAUTION]
Only run this if you have enough knowledge about the security implications of running arbitrary commands in your virtual machine.
**Never run this on your local machine**. You are letting the AI/LLM pilot run commands in your machine and it can be dangerous. Additionally, there is a risk that the AI might interact with the external world, and be taken over by an attacker.

## Overview

VMPilot is an AI-driven system operations assistant that provides command execution capabilities in virtual machines through CLI and API interfaces. It enables users to delegate terminal tasks to an AI/LLM pilot powered by Claude 3.5 Sonnet, which can execute multiple commands to accomplish requested operations. The system features real-time response streaming, comprehensive error handling, and robust security measures, while offering both command-line and API access methods.

It is available as an Open WebUI Pipeline, or a cli.

It is derived from [Claude Computer Use](https://docs.anthropic.com/en/docs/build-with-claude/computer-use) and [OpenWebUI Pipelines](https://docs.anthropic.com/en/docs/build-with-claude/openwebui-pipelines).

## Dependencies

Core dependencies:
- Python 3.11+
- OpenWebUI Pipelines
- Other dependencies as specified in requirements.txt

To install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
.
├── compute.py     -- Main pipeline implementation
├── loop.py        -- Core agent loop for LLM interaction
├── logger.py      -- Logging configuration
└── tools/
    ├── base.py    -- Base tool implementations
    ├── bash.py    -- Bash command execution tool
    └── ...
```


## Features

### Core Features
- System prompt handling through message history
  - Extracts and applies system prompts from conversation context
  - Preserves system instructions across interactions

- Code Output Processing
  - Automatic programming language detection
  - Smart code fence wrapping (\`\`\`language)
  - Fallback to plain text for unknown content

- Streaming Support
  - Real-time response streaming
  - Async queue-based implementation
  - Support for both streaming and single-response modes

- Tool Integration
  - Structured tool output handling
  - Error code and message capture
  - Exit status reporting

- Model Support
  - Currently using Claude 3.5 Sonnet
  - Extensible to other API providers

## Installation

To use the pipeline:

1. Install dependencies

2. Configure the ANTHROPIC_API_KEY environment variable
3. The pipeline runs on port 9099 by default
4. Access through any OpenAI API-compatible client

## Security Considerations

- The pipeline has arbitrary code execution capabilities
- Should only be used in trusted environments
- Keep API keys secure
- Follow standard security practices when exposing endpoints

## Error Handling

The pipeline provides:
- Detailed error messages
- Exit code reporting
- Syntax-highlighted error output
- Proper cleanup on failures

## Logging

Comprehensive logging includes:
- Tool execution details
- API interactions
- Error conditions
- Performance metrics

## Key Components

### vmpilot.py

The main pipeline implementation that:
- Provides an OpenAI API-compatible endpoint
- Handles message streaming
- Manages tool execution
- Features automatic code language detection and syntax highlighting
- Supports both streaming and non-streaming responses

### loop.py

Core agent loop implementation that:
- Manages interactions between LLMs and computer control tools
- Supports multiple API providers (Anthropic, etc.)
- Handles conversation context and tool execution
- Implements prompt caching and optimization
- Provides robust error handling

