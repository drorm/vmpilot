# Available plugins

Alls plugins as well as the main README.md are located in $VMPILOT_ROOT/src/vmpilot/plugins.

# Github

directory: github\_issues
- To view or list issues, use "$PROJECT_ROOT/src/vmpilot/plugins/github_issues/gh_issue.sh  view $number" or use this gh_issue.sh command as a replacement for any other "gh" command.
- To create an issue view the README.md file for instructions.

# Documentation

directory: documentation
- Provides guidance for creating clear, concise, and user-friendly documentation

# Testing

directory: testing
- Provides guidance for the VMPilot testing ecosystem as part of the CI/CD workflow
- Testing is an integral part of development, not an optional activity
- Includes unit tests, end-to-end tests, and coverage analysis requirements

# Code Review
directory: code_review
- Provides guidelines for conducting code reviews within the project, to ensure code quality, consistency, and maintainability 

# Branch Manager

directory: branch_manager
- Automates the process of creating git branches for issues and updating project context
- Use `create_branch.sh <issue_number>` to create a branch for an issue
