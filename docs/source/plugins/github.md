# GitHub Plugin

The GitHub plugin is a crucial component of VMPilot that enables integration with GitHub's issue tracking system. It allows you to create, view, and manage GitHub issues directly from your VMPilot sessions, providing continuity and context for your development tasks.

## Overview

This plugin leverages the GitHub CLI (`gh`) to interact with GitHub repositories. It enables VMPilot to:

- Create new issues with appropriate templates and labels
- View existing issues and their details
- Comment on issues to track progress
- Close and reopen issues as needed

## Why It Matters

The GitHub plugin transforms how you work with VMPilot by providing several key benefits:

1. **Context Preservation**: Start a chat with "look at issue 123" to instantly provide context to the LLM about what you're working on, eliminating the need to repeatedly describe the same task.

2. **Structured Problem Definition**: Collaborate with the LLM to articulate what you're trying to accomplish, to flesh out the details.

3. **Progress Tracking**: Adding comments to issues creates a timeline of your work, helping the LLM keep track of the progress and decisions.

4. **Collaborative Workflow**: Even when working alone with the LLM, you can use issues in the same way a team of developers would collaborate, providing a structured approach to development.

## Prerequisites

To use the GitHub plugin, you need:

- GitHub CLI (`gh`) installed and configured on your system
- Authentication with GitHub (`gh auth login`)
- A GitHub repository 

## Common Commands

### Viewing Issues

To view an issue and its details:

```bash
look at issue 16
```

To see comments associated with an issue:

```bash
look at issue 16 with comments
```

To list all open issues:

```bash
show me all open issues
```

### Creating Issues

To create a new issue:

```bash
Let's discuss creating "new feature".
```

VMPilot will:
1. Ask you clarifying questions about the issue
2. Guide you through filling out the required fields based on issue templates
3. Confirm with you before creating the issue
4. Provide the issue number and link once created

### Commenting on Issues

To add a comment to an existing issue:

```bash
add comment to issue 16: "Implemented the first part of this feature"
```

## Workflow Example

Here's a typical workflow using the GitHub plugin:

1. **Start a task by creating an issue**:
   ```
   create a github issue titled "Implement documentation plugin"
   ```

2. **Begin work with context**:
   ```
   look at issue 25. Look at the code in file.py and ...
   ```

3. **As you make progress, add comments**:
   ```
   add comment to issue 25: "Created the initial plugin structure"
   ```

4. **Close the issue when complete**:
   ```
   close issue 25 with comment "Feature completed and tested"
   ```


## Integration with Development Process

The GitHub plugin enables a structured development approach even for solo developers:

- **Task Definition**: Issues clearly define what needs to be done
- **Work History**: Comments provide a record of decisions and progress
- **Knowledge Retention**: Closed issues serve as documentation for how problems were solved
- **Continuity**: New VMPilot sessions can quickly pick up context from previous work
