# Welcome to VMPilot

[TOC]

VMPilot is a chat-based AI development agent that operates directly in your virtual machine environment. It combines natural language understanding with the ability to perform complex development tasks - reading and modifying code, managing GitHub issues, and executing system commands. Powered by OpenWebUI's rich chat interface, it provides an intuitive way to interact with your development environment through workspaces, advanced chat features, and support for multiple AI models.

> [!CAUTION]
> Only run this if you have enough knowledge about the security implications of running arbitrary commands in your virtual machine.
> **Never run this directly on your personal machine**. You are letting the AI/LLM pilot run commands in your machine and it can be dangerous.

## Key Features

🔹 **Full System Access**
- Operates directly within your virtual machine environment
- Executes and chains system commands intelligently
- Manages files, services, and system operations
- Understands your entire development environment

🔹 **End-to-End Development Support**
- Works directly in your development environment
- Writes and modifies code based on your requirements
- Reads and analyzes test outputs to guide fixes
- Integrates with GitHub for issue management
- Understands project context and maintains consistency

🔹 **Extensible Plugin Architecture**
- Built-in GitHub integration for issues and code management
- Plugin system ready for custom workflow extensions
- Future plugins planned for documentation and testing

🔹 **Multiple Interfaces & OpenWebUI Integration**
- Powerful CLI for terminal-based workflows
- Rich web interface with advanced features:
  - Multi-modal conversation view with code highlighting
  - Real-time streaming responses
  - Conversation history and context management
  - Workspace organization and customization
  - Support for multiple LLM providers

## Quick Start Guide

Get up and running with VMPilot in minutes:

1. [Installation](installation.md) - Set up VMPilot on your system
2. [Configuration](configuration.md) - Configure your environment
3. [User Guide](user-guide.md) - Learn the basics of VMPilot

## Core Documentation

### Essential Guides
- [Prompting Guide](prompting.md) - Master effective prompt writing for VMPilot
- [Tips and Best Practices](tips.md) - Learn proven techniques and best practices
- [CLI Reference](cli.md) - Complete command-line interface documentation

### Tools and Extensions
- [Plugins](plugins.md) - Extend VMPilot's capabilities with plugins
- [GitHub Issues](github_issues.md) - Streamline GitHub issue management
- [DNS and SSL Setup](dns_ssl_setup.md) - Secure your VMPilot deployment
