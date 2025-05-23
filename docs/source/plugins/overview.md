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
- Helps users work with the MkDocs documentation system used by VMPilot
- Offers best practices for technical writing and content structure
- Assists with formatting for readability and proper Markdown usage

# Testing

directory: testing
- Provides guidance for the VMPilot testing ecosystem as part of the CI/CD workflow
- Includes unit tests, end-to-end tests, and coverage analysis requirements
- Testing is an integral part of development, not an optional activity

# Project

directory: project
- Manages project-specific configuration through the .vmpilot directory structure
- Creates and maintains project context files (like project.md) that persist across conversations
- Provides a framework for project documentation and setup
- Streamlines the onboarding experience for new projects
- Automatically includes project.md in the system prompt for each conversation

# Branch Manager

directory: branch_manager
- Automates the process of creating git branches for GitHub issues
- Ensures consistent branch naming conventions across the project
- Integrates with GitHub to fetch issue details and create appropriate branches
- Streamlines the workflow when starting work on a new issue
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
