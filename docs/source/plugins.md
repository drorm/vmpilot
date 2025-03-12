# Plugins

VMPilot uses a unique text-based plugin system that extends LLM functionality without requiring traditional code-based implementations. This approach makes plugins easy to add, remove, and maintain.

## How Plugins Work

Instead of using code-based integrations, VMPilot plugins work by injecting the plutin's directory README.md that lists the plugins into the main prompt. When the llm needs to access a plugin, it reads the README.md for that plugin and knows what actions are available.

For example, the `github_issues` plugin enables GitHub issue management through simple text commands. This plugin could be easily replaced with alternatives (like a Jira plugin) by swapping the plugin configuration.

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


