# VMPilot

## Overview

VMPilot is:
- your pair programming partner.
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

For detailed information about VMPilot's features and capabilities, check out:

- [Installation Guide](docs/installation.md) - Complete setup instructions
- [Configuration Guide](docs/configuration.md) - Configure VMPilot for your needs
- [User Guide](docs/user-guide.md) - Learn how to use VMPilot effectively
- [Security Guide](docs/security.md) - Understanding and managing security implications
- [Plugin Development](docs/plugins.md) - Extend VMPilot's capabilities


