# Plugins

VMPilot uses a unique text-based plugin system that extends LLM functionality without requiring traditional code-based implementations. This approach makes plugins easy to add, remove, and maintain.

## How Plugins Work

Instead of using code-based integrations, VMPilot plugins work by injecting the plugin's directory README.md that lists the plugins into the main prompt. When the LLM needs to access a plugin, it reads the README.md for that plugin and knows what actions are available.

For example, the `github_issues` plugin enables GitHub issue management through simple text commands. This plugin could be easily replaced with alternatives (like a Jira plugin) by swapping the plugin configuration.

## VMPilot-Specific Implementation

The plugin system design is based on VMPilot's own development stack:
- **GitHub**: Issue tracking and workflow management
- **Python**: Backend implementation language
- **Backend-focused**: Designed for system operations tasks

Other projects should adapt this plugin system to their specific tech stack and needs. The text-based approach makes it highly adaptable to different environments, languages, and toolchains.

## Current Plugin System

The system currently looks like this:
```markdown

# Available plugins

# Codemap
directory: codemap
Creates documentation by scanning the code and generating a doc per source file.

# Github

directory: github\_issues
- To view or list issues, use "cd $rootDir && gh issue view $number" or "gh issue list". Always include the "gh" command.
- To create an issue view the README.md file for instructions.

# Documentation

directory: documentation
- Provides guidance for creating clear, concise, and user-friendly documentation

# Unit Testing

directory: unit_testing
- Provides guidance for creating comprehensive unit tests for VMPilot components
- Includes test templates and best practices for effective test implementation
```

## Managing Plugins

Enabling or disabling plugins is straightforward - simply add or remove their entries from the main README.md file.

## Creating New Plugins

To create a new plugin:
1. Create a directory in the plugins directory
2. Create a README.md file using template.md from the plugins directory as a guide
3. Add your plugin's entry to the main README.md file in the plugins directory
4. Test the plugin functionality with various prompts

For examples of existing plugins, see the `codemap` and `github_issues` implementations in the plugins directory.

## Adapting to Other Projects

When implementing this plugin system in your own projects:

1. **Use VMPilot**: Ask VMPilot to look at the plugin system and adapt it to your project
2. **Evaluate your stack**: Consider which tools and platforms your project relies on
3. **Identify integration points**: Determine which aspects of your workflow would benefit from LLM assistance
4. **Design plugin interfaces**: Create clear, concise instructions that tell the LLM how to interact with your tools
5. **Start simple**: Begin with basic plugins and expand functionality as needed

The flexibility of text-based plugins allows for easy experimentation and iteration without significant code changes.
