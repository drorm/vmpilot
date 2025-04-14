# Branch Manager Plugin

The Branch Manager Plugin automates Git branch creation for GitHub issues, streamlining the workflow between issue tracking and development. 

## Purpose

This plugin helps developers:

- Create properly named Git branches for GitHub issues
- Follow consistent branch naming conventions
- Avoid common errors like duplicate branches
- Streamline the workflow when starting work on a new issue

**Branch creation is initiated by the user, and the plugin handles the rest.**

## Features

The Branch Manager provides several key capabilities:

- **Automated Branch Creation**: Creates and pushes branches with proper naming conventions
- **Issue Integration**: Fetches issue details directly from GitHub
- **Conflict Detection**: Checks if branches already exist locally or remotely
- **Similar Issue Detection**: Prevents confusion between similar issue numbers (e.g., issue-34 vs issue-334)
- **Error Handling**: Provides informative output for troubleshooting

## Branch Naming Convention

When creating branches, the plugin follows these rules:

- Starts with a lowercase category (feature, bug, docs, chore, etc.)
- Includes the issue number
- Adds a short, hyphen-separated summary derived from the issue title
- Replaces spaces with hyphens
- Uses all lowercase
- Supports both dash and slash separators (e.g., `feature-65` or `feature/65`)

Example: `feature/65-implement-vmpilot-prompts`

## Usage

### Creating a Branch for an Issue

To create a branch for a GitHub issue, just ask VMPilot to use the Branch Manager Plugin to create the branch for the issue number you provide. 


## Workflow Integration

The Branch Manager Plugin integrates seamlessly with VMPilot's workflow:

1. **Issue Assignment**: A GitHub issue is assigned to you
2. **Branch Creation**: Use the plugin to create a properly named branch
3. **Development**: Make your changes on the new branch
4. **Pull Request**: Create a PR when your changes are ready for review

This workflow ensures that all code changes are properly tracked and linked to their corresponding issues.

