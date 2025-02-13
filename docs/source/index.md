# VMPilot Documentation

> [!CAUTION]
> Only run VMPilot in a dedicated virtual machine. Never run this on your local machine as it allows AI/LLM to execute arbitrary commands which can be dangerous. There are security risks including potential external world interactions that could be exploited by attackers.

## What is VMPilot?

VMPilot provides a way to interact with an AI agent to perform tasks in a virtual machine. It is focused on pair programming, where the AI can help you with coding tasks, but it can also be used for other system operations. While using a familiar chat interface (thanks to OpenWebUI), it provides advanced capabilities by executing multiple commands in the virtual machine to accomplish your requested tasks.

Using natural language, you can ask VMPilot to:
- Write and modify code
- Execute system commands
- Manage files and directories
- Handle GitHub issues and repositories
- Perform complex multi-step operations

## Available Interfaces

VMPilot can be used in two ways:
- **Web Interface**: Full-featured interface through OpenWebUI integration 
- **CLI Mode**: Direct command-line interface for quick interactions. This is mostly used for testing and debugging.

## Key Features

- **Intelligent Command Execution**: 
  - Natural language understanding of your intent
  - Smart handling of complex multi-step operations
  - Real-time feedback and error handling
  
- **Development Tools**:
  - Code writing and modification
  - File management and editing
  - GitHub integration for issue management
  
- **Flexible LLM Support**:
  - Works with multiple providers (Anthropic, OpenAI)
  - Configurable models and parameters
  - Streaming response capability

## Getting Started

1. [Installation Guide](installation.md) - Complete setup instructions
2. [Configuration Guide](configuration.md) - Configure VMPilot for your needs
3. [User Guide](user-guide.md) - Learn the basics of using VMPilot

## Documentation Sections

### Essential Guides
- [Configuration Guide](configuration.md) - Setting up VMPilot
- [Installation Guide](installation.md) - Detailed installation steps
- [User Guide](user-guide.md) - Basic usage and concepts

### Advanced Topics
- [Prompting Guide](prompting.md) - How to effectively interact with VMPilot
- [Plugins System](plugins.md) - Extending VMPilot's capabilities
- [GitHub Integration](github_issues.md) - Working with GitHub repositories
- [Tips and Best Practices](tips.md) - Advanced usage tips

## Security Considerations

VMPilot has powerful capabilities that require careful consideration:

- Only run in isolated virtual machines
- Keep API keys secure and use fine-grained access tokens
- Follow security best practices when exposing endpoints
- Regularly monitor and audit command execution
- Use minimal permissions for GitHub and other integrations
