# VMPilot

## Overview

VMPilot is:
- your pair programming partner
- virtual machine based: it reads, writes, and performs various actions on files and run commands in the virtual machine.
- an agent. It runs multiple commands to perform a task. It’ll for instance run a unit test, see an error, fix it, and keep making changes until there are no errors.
- web based with a very advanced and powerful UI curtsy of OpenWebUI.
- extensible. Using plugins it targets the full life cycle of software development: creating issues, coding, testing, documenting, etc.


> [!CAUTION]
Only run this if you have enough knowledge about the security implications of running arbitrary commands in your virtual machine.
**Never run this on your personal machine**. You are letting the AI/LLM pilot run commands in your machine and it can be dangerous. Additionally, there is a risk that the AI might interact with the external world, and be taken over by an attacker.

## What can you do with VMPilot?

Using natural language, you can ask VMPilot to:
- Create Github issues
- Write and modify code
- Create and run tests
- Create and update documentation
- Manage git repositories
- Perform system operations

## Features

### Core Features
- The rich and advanced features of [OpenWebUI](https://github.com/open-webui/open-webui/)
- Code Output Processing Automatic programming language detection,smart code fence wrapping
- Streaming Support. Support for both streaming and single-response modes
- Model Support
  - Primarily tested with Claude 3.5 Sonnet
  - OpenAI API gpt4-o support

## Documentation

### Getting Started
- [Installation Guide](docs/source/installation.md) - Complete setup instructions
- [Configuration Guide](docs/source/configuration.md) - Customize your environment
- [User Guide](docs/source/user-guide.md) - Learn the basics

### Core Features
- [Command Line Interface](docs/source/cli.md) - Using the CLI effectively
- [Prompting System](docs/source/prompting.md) - Understanding context management
- [Tips and Best Practices](docs/source/tips.md) - Optimize your workflow

### Advanced Topics
- [DNS and SSL Setup](docs/source/dns_ssl_setup.md) - Secure access configuration
- [Plugins System](docs/source/plugins.md) - Extend functionality
- [GitHub Issues Integration](docs/source/github_issues.md) - Issue management
