# Available plugins

Alls plugins as well as the main README.md are located in $VMPILOT_ROOT/src/vmpilot/plugins.

# Github

directory: github\_issues
<<<<<<< HEAD
- To view or list issues, use "cd $rootDir && gh issue view $number -c" or "gh issue list". Always include the "gh" command.
=======
- To view or list issues, use "$PROJECT_ROOT/src/vmpilot/plugins/github_issues/gh_issue.sh  view $number" or use this gh_issue.sh command as a replacement for any other "gh" command.
>>>>>>> dev
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

# Project

directory: project
- Manages project-specific configuration through the .vmpilot directory structure
- Creates and maintains project context files that persist across conversations
- Provides a framework for project documentation and setup

# Branch Manager

directory: branch_manager
- Automates the process of creating git branches for issues and updating project context
- Use `create_branch.sh <issue_number>` to create a branch for an issue
