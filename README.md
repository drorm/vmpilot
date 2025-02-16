# VMPilot

> [!CAUTION]
Only run this if you have enough knowledge about the security implications of running arbitrary commands in your virtual machine.
**Never run this on your local machine**. You are letting the AI/LLM pilot run commands in your machine and it can be dangerous. Additionally, there is a risk that the AI might interact with the external world, and be taken over by an attacker.

## Overview

Overview: VMPilot is an AI-driven assistant designed to perform tasks within a virtual machine by interacting with an intelligent agent. Originally developed to support pair programming, it not only aids with coding but also handles various other operations. Its user interface resembles popular chat interfaces, yet it extends functionality by executing multiple commands to fulfill your requests. VMPilot is available both as an Open WebUI Pipeline and as a command-line interface.

It is inspired by [Claude Computer Use](https://docs.anthropic.com/en/docs/build-with-claude/computer-use) and uses [OpenWebUI Pipelines](https://docs.anthropic.com/en/docs/build-with-claude/openwebui-pipelines).

## Features

### Core Features
- The rich and advanced features of OpenWebUI 
- Code Output Processing Automatic programming language detection,smart code fence wrapping 
- Streaming Support. Support for both streaming and single-response modes
- Tool Integration Structured tool output handling
- Model Support
  - Primarily tested with Claude 3.5 Sonnet
  - OpenAI API gpt4-o support
  - Extensible to other API providers

## Installation

For a complete setup, follow these guides in order:

1. [DNS and SSL Setup](docs/dns_ssl_setup.md) - Optional, but highly recommended to configure secure access to your services
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

### agent.py

Core agent implementation that:
- Manages interactions between LLMs and computer control tools
- Supports multiple API providers (Anthropic, OpenAI)
- Handles conversation context and tool execution
- Implements prompt caching and optimization
- Provides robust error handling
