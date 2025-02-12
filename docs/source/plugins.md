# Plugins

VMPilot plugins provide a unique approach to extending LLM functionality through text-based configuration, rather than traditional code-based plugins.
This means that it is quite easy to add or remove plugins from the system, and the plugins themselves are simple to create and maintain.

We use, for instance, the `github issues` plugin to manage issues in the VMPilot project. It should be relatively easy to replace it with a different plugin, such as a Jira plugin, if needed.

## How Plugins Work

The system injects each plugin's README.md content into the LLM's prompt. Currently, the plugin system looks like this:
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

Enabling or disabling plugins is straightforward - simply add or remove their entries from the README.md file.

## Creating New Plugins

To create a new plugin:
1. Create a directory in the plugins directory
2. Create a README.md file using template.md from the plugins directory as a guide
3. Add your plugin's entry to the main README.md file in the plugins directory
4. Test the plugin functionality with various prompts

For examples of existing plugins, see the `codemap` and `github_issues` implementations in the plugins directory.


