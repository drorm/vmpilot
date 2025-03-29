#!/bin/bash

# Get the git root directory
GIT_ROOT=$(git rev-parse --show-toplevel)

echo "Setting up Git hooks..."

# Ensure .git-hooks directory exists
mkdir -p "$GIT_ROOT/.git-hooks"

# Create pre-commit hook in .git-hooks
cat > "$GIT_ROOT/.git-hooks/pre-commit" << 'EOF'
#!/bin/bash

# Get the git root directory
GIT_ROOT=$(git rev-parse --show-toplevel)

# Execute the lint.sh script
"$GIT_ROOT/sh/lint.sh"

# Exit with the same status as the lint script
exit $?
EOF

# Make it executable
chmod +x "$GIT_ROOT/.git-hooks/pre-commit"

# Create symlink for pre-commit hook
ln -sf "../.git-hooks/pre-commit" "$GIT_ROOT/.git/hooks/pre-commit"

echo "Git hooks setup complete. The lint.sh script will run before each commit."
