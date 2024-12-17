# Compute Pipeline

> [!CAUTION]
Only run this if you have enough knowledge about the security implications of running arbitrary commands in your virtual machine.
**Never run this on your local machine**. You are letting the AI/LLM pilot run commands in your machine and it can be dangerous. Additionally, there is a risk that the AI might interact with the external world, and be taken over by an attacker.

## Overview

VMPilot provides a way to interact with an AI agent to perform tasks in a virtual machine. It is focused on pair programming, where the AI can help you with coding tasks, but it can also be used for other tasks as well.
While the UI is similar to the chat interface of OpenAI and other AI models (thanks to OpenWebUI), it provides advanced capabilities by executing multiple commands in the virtual machine to accomplish the requested task.
It is is available as an Open WebUI Pipeline, or a cli.

It is inspired by [Claude Computer Use](https://docs.anthropic.com/en/docs/build-with-claude/computer-use) and uses [OpenWebUI Pipelines](https://docs.anthropic.com/en/docs/build-with-claude/openwebui-pipelines).

## Dependencies

Core dependencies:
- Python 3.11+
- OpenWebUI Pipelines
- Other dependencies as specified in requirements.txt

To install dependencies:
```bash
pip install -r requirements.txt
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
  - Primarily tested with Claude 3.5 Sonnet
  - OpenAI API gpt4o support

## Installation

For a complete setup, follow these guides in order:

1. [DNS and SSL Setup](docs/dns_ssl_setup.md) - Configure secure access to your services
2. [Installation Guide](docs/installation.md) - Full installation instructions including OpenWebUI and pipeline setup
3. [Usage Guide](docs/usage.md) - Learn how to use VMPilot effectively

Quick start:
1. Install dependencies (`pip install -r requirements.txt`)
2. Configure the ANTHROPIC_API_KEY environment variable
3. The pipeline runs on port 9099 by default
4. Access through any OpenAI API-compatible client

See the [Installation Guide](docs/installation.md) for detailed setup instructions.

## Security Considerations

- The pipeline has arbitrary code execution capabilities
- Should only be used in trusted environments
- Keep API keys secure
- Follow standard security practices when exposing endpoints

When using VMPilot with GitHub repositories, it's crucial to follow security best practices to protect your account and repositories:

### Use Fine-Grained Personal Access Tokens

Instead of using tokens with full repository access:

1. Go to GitHub Settings > Developer Settings > Personal Access Tokens > Fine-grained tokens
2. Create a new token with:
   - Limited repository access (only select required repositories)
   - Minimal permissions (e.g., only Contents:Read if just cloning)
   - Set an expiration date

### Permission Scopes

Only grant the minimal permissions needed:
- For read-only operations: `Contents: Read`
- For cloning and pulling: `Contents: Read`
- For committing changes: `Contents: Read & Write`

### Security Recommendations

- Never share tokens with full repository access
- Regularly rotate access tokens
- Monitor token usage in GitHub Security settings
- Revoke tokens immediately if compromised
- Use separate tokens for different purposes/repositories

### Token Environment Variables

When configuring GitHub access:
```bash
# Use specific environment variables for different access levels
GITHUB_READ_TOKEN=github_pat_xxx  # Read-only access
GITHUB_WRITE_TOKEN=github_pat_yyy # Repository write access
```

This approach ensures that even if a token is compromised, the potential impact is limited to specific repositories and actions.

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
