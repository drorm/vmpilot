# GitHub Issues Plugin

The GitHub Issues plugin seamlessly integrates GitHub issue management into VMPilot through the GitHub CLI (`gh`). This integration allows you to manage GitHub issues using natural language commands without leaving your VMPilot environment.
The most valuable use of this plugin is to be able to reference the issues when collaborating with the LLM.

## Prerequisites

Before using this plugin, ensure:
- GitHub CLI (`gh`) is installed in the virutal machine
- You have completed GitHub CLI authentication (`gh auth login`)
  - Optional, but recommended, create a separate GitHub identity for VMPilot

## Features

### Viewing Issues

View issues using natural language commands:
```
show me issue 3
show the status of issue #5
list all open issues
```

The plugin handles all necessary steps:
1. Navigates to the project root directory
2. Executes the appropriate GitHub CLI commands
3. Displays formatted issue information

### Creating Issues

Create new issues using conversational requests:
```
create a github issue titled "Add logging feature" with label "enhancement"
```

The plugin streamlines the creation process:
1. Follows repository issue templates
2. Collects required information through interactive prompts
3. Creates the issue via GitHub CLI

### Supported Operations

The plugin handles essential GitHub issue management:
- Viewing issue details
- Creating new issues
- Listing all issues (open/closed)
- Updating issue status
- Managing labels and assignments

## Best Practices

1. **Clear Communication**
   - Use specific, descriptive issue titles
   - Provide detailed descriptions
   - Reference relevant code or documentation

2. **Proper Organization**
   - Apply appropriate labels
   - Follow repository issue templates
   - Include necessary context

3. **Workflow Guidelines**
   - Verify issue details before creation
   - Use consistent formatting
   - Follow repository conventions

## Examples

### View an Issue
```
show me issue #3
```

### Create a Feature Request
```
create an issue:
title: Add dark mode support
label: enhancement
description: Implement dark mode theme for better visibility in low-light conditions
```

### List Issues
```
show open issues with label "bug"
list all issues assigned to me
```

The plugin automatically handles the GitHub CLI commands and provides formatted responses for all operations.

## Technical Implementation

The plugin:
- Uses the project root as the working directory
- Interfaces with GitHub through the CLI
- Follows repository-specific templates
- Provides interactive feedback
- Validates operations before execution
