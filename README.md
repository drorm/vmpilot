# VMPilot

VMPilot is a chat based AI development agent that operates directly in your virtual machine environment. It combines natural language understanding with the ability to perform complex development tasks - reading and modifying code, managing GitHub issues, and executing system commands. Powered by OpenWebUI's rich chat interface, it provides an intuitive way to interact with your development environment through workspaces, advanced chat features, and support for multiple AI models.

> [!CAUTION]
Only run this if you have enough knowledge about the security implications of running arbitrary commands in your virtual machine.
**Never run this directly on your personal machine**. You are letting the AI/LLM pilot run commands in your machine and it can be dangerous. Additionally, there is a risk that the AI might interact with the external world, and be taken over by an attacker.

## Why VMPilot?

While many AI coding assistants focus solely on code completion, VMPilot operates at the system level, providing comprehensive automation and assistance across your entire development environment:

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
- Future plugins planned for documentation and testing (coming soon)

🔹 **Multiple Interfaces**
- Powerful CLI for terminal-based workflows
- Rich web interface through OpenWebUI

## Powerful Web Interface with OpenWebUI

VMPilot leverages OpenWebUI to provide a superior development experience:

🚀 **Advanced Chat Interface**
- Multi-modal conversation view with code highlighting
- Real-time streaming responses
- Conversation history and context management
- Edit and refine prompts on the fly
- Stop and control AI responses at any time

⚙️ **Workspace Organization**
- Create dedicated workspaces for different projects or tasks
- Maintain separate contexts for frontend and backend development
- Switch between different LLM providers (OpenAI, Anthropic) per conversation
- Save and reuse effective prompts and configurations

🎛️ **Extensive Customization**
- Fine-tune model parameters and behavior
- Configure UI preferences and layout
- Customize syntax highlighting and themes
- Adjust token limits and other technical settings

## Documentation

Check out the documentation, including setup guides, architecture details, and usage examples in our [documentation site](https://drorm.github.io/vmpilot/).

## Development Status

VMPilot is under active development. While it's stable for general use, we're continuously adding features and improvements. Check our [GitHub Issues](https://github.com/drorm/vmpilot/issues) for current development status and planned features.
