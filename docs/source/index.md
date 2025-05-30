# Welcome to VMPilot

[TOC]

VMPilot is a chat-based AI development agent that operates directly in your virtual machine environment. It combines natural language understanding with the ability to perform complex development tasks - reading and modifying code, managing GitHub issues, and executing system commands. Powered by OpenWebUI's rich chat interface, it provides an intuitive way to interact with your development environment through workspaces, advanced chat features, and support for multiple AI models.

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
- Supports multi-branch development with workspace isolation

🔹 **Extensible Plugin Architecture**

- Built-in GitHub integration for issues and code management
- Plugin system ready for custom workflow extensions
- Future plugins planned for documentation and testing

🔹 **Multiple Interfaces & OpenWebUI Integration**

- Powerful CLI for terminal-based workflows
- Bundled Open WebUI for a seamless installation experience
- Rich web interface with advanced features:
  - Multi-modal conversation view with code highlighting
  - Real-time streaming responses
  - Conversation history and context management
  - Workspace organization and customization
  - Support for multiple LLM providers
  - Supports continuous CLI chat sessions with the `-c` flag when data is stored in SQLite

## Quick Start Guide

Get up and running with VMPilot in minutes:

1. [Installation](installation.md) - Set up VMPilot on your system
2. [Getting Started](getting-started.md) - Learn the basics of VMPilot
3. [Using Open WebUI](using-webui.md) - Learn how to use the web interface effectively
4. [Configuration](configuration.md) - Configure your environment

## Core Documentation

### Essential Guides
- [Prompting Guide](prompting.md) - Master effective prompt writing for VMPilot
- [CLI Reference](cli.md) - Complete command-line interface documentation

### Tools and Extensions
- [Plugins](plugins/overview.md) - Extend VMPilot's capabilities with plugins
- [GitHub Issues](plugins/github.md) - Streamline GitHub issue management
- [DNS and SSL Setup](dns_ssl_setup.md) - Secure your VMPilot deployment
