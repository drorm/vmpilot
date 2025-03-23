#!/bin/bash

# Get the git root directory
GIT_ROOT=$(git rev-parse --show-toplevel)

echo "Setting up Git hooks..."

# Create symlink for pre-commit hook
ln -sf "../git-hooks/pre-commit" "$GIT_ROOT/.git/hooks/pre-commit"
chmod +x "$GIT_ROOT/.git/hooks/pre-commit"

echo "Git hooks setup complete. The pre-commit hook will run before each commit."