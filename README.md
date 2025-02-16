# VMPilot

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

VMPilot is:
- your pair programming partner
- virtual machine based: it reads, writes, and performs various actions on files and run commands in the virtual machine.
- an agent. It runs multiple commands to perform a task. It’ll for instance run a unit test, see an error, fix it, and keep making changes until there are no errors.
- web based with a very advanced and powerful UI curtsy of OpenWebUI.
- extensible. Using plugins it targets the full life cycle of software development: creating issues, coding, testing, documenting, etc.

> [!CAUTION]
Only run this if you have enough knowledge about the security implications of running arbitrary commands in your virtual machine.
**Never run this directly on your personal machine**. You are letting the AI/LLM pilot run commands in your machine and it can be dangerous. Additionally, there is a risk that the AI might interact with the external world, and be taken over by an attacker.

## What can you do with VMPilot?

Using natural language, you can ask VMPilot to:
- Create Github issues
- Write and modify code
- Create and run tests
- Create and update documentation
- Manage git repositories
- Perform system operations

## Documentation

Check out the documentation, including setup guides, architecture details, and usage examples in our [documentation site](https://drorm.github.io/vmpilot/).

## Development Status

VMPilot is under active development. While it's stable for general use, we're continuously adding features and improvements. Check our [GitHub Issues](https://github.com/drorm/vmpilot/issues) for current development status and planned features.
