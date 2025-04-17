#!/bin/bash

# Get the git root directory
GIT_ROOT=$(git rev-parse --show-toplevel)

echo "Setting up Git hooks..."

# Create pre-commit hook directly in .git/hooks
cat > "$GIT_ROOT/.git/hooks/pre-commit" << EOF
#!/bin/bash

echo "Pre-commit hook is running!"

# Use direct path to the lint.sh script
$GIT_ROOT/sh/lint.sh

# Exit with the same status as the lint script
exit \$?
EOF

# Make it executable
chmod +x "$GIT_ROOT/.git/hooks/pre-commit"

echo "Git hooks setup complete. The lint.sh script will run before each commit."
