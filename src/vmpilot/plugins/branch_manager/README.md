# Branch Manager Plugin for VMPilot

This plugin automates the process of creating git branches for issues and updating the project's current issue context.

## Features

- Creates and pushes branches with proper naming conventions
- Checks if branches already exist (locally or remotely) before creating
- Detects similar issue numbers to prevent confusion (e.g., issue-34 vs issue-334)
- Uses GitHub CLI directly for fetching issue information
- Handles errors gracefully and provides informative output

## When to Use This Plugin

Use this plugin when:

1. A user wants to start working on a GitHub issue
2. A user mentions working on a new feature or bug fix that has an associated issue
3. A user asks to create a branch for an issue
4. A user wants to know what issue they're currently working on

## Branch Naming Convention

When generating a branch name, follow these rules:
- Start with a lowercase category (feature, bug, docs, chore, etc.)
- Include the issue number
- Add a short, hyphen-separated summary (limit to 40 characters)
- Replace spaces with hyphens
- Use all lowercase
- You can use either dashes or slashes between the category and issue number (e.g., feature-65 or feature/65)
- Example: `feature/65-implement-vmpilot-prompts`

## Commands

### Create Branch

```bash
/home/dror/vmpilot/src/vmpilot/plugins/branch_manager/create_branch.sh <issue_number> [issue_type]
```

This command:
- Takes an issue number as a required parameter
- Accepts an optional issue type parameter (feature, bug, docs, chore, etc.)
  - Default is "feature" if not specified
- Fetches the issue details using GitHub CLI (gh)
- Generates an appropriate branch name based on the issue title and type
- Switches to the dev branch automatically
- Checks if the branch already exists:
  - If it exists, switches to the existing branch
  - If similar branches exist (with the same issue number), asks for confirmation
  - Otherwise, creates a new branch
- Creates and pushes the branch
- Provides detailed error information if any step fails

#### Examples:

```bash
# Create a feature branch for issue #65
/home/dror/vmpilot/src/vmpilot/plugins/branch_manager/create_branch.sh 65

# Create a bug branch for issue #42
/home/dror/vmpilot/src/vmpilot/plugins/branch_manager/create_branch.sh 42 bug

# Create a documentation branch for issue #73
/home/dror/vmpilot/src/vmpilot/plugins/branch_manager/create_branch.sh 73 docs
```
