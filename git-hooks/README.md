# Git Hooks

This directory contains Git hooks for the VMPilot project.

## Available Hooks

- **pre-commit**: Runs linting checks (black and isort) before each commit

## Setup

To set up the Git hooks, run the setup script:

```bash
./git-hooks/setup.sh
```

This will create symbolic links in your local `.git/hooks` directory pointing to the hook scripts in this repository.

## Manual Installation

If you prefer to set up the hooks manually:

1. For the pre-commit hook:
   ```bash
   ln -s ../git-hooks/pre-commit .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```