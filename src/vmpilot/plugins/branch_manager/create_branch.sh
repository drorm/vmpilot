#!/bin/bash

# This script creates a git branch for an issue and sets it as the current issue

# Don't exit on error to allow for proper error handling
set +e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo $PWD)}"

# Function to display usage information
function show_usage {
    echo "Usage: $0 <issue_number> [issue_type]"
    echo "Creates a git branch for the given issue number"
    echo ""
    echo "Arguments:"
    echo "  issue_number    Required: The GitHub issue number"
    echo "  issue_type      Optional: Type of issue (feature, bug, docs, chore, etc.)"
    echo "                  Default: feature"
    echo ""
    echo "Examples:"
    echo "  $0 65"
    echo "  $0 65 bug"
    exit 1
}

# Check if at least issue number was provided
if [ $# -lt 1 ]; then
    show_usage
fi

ISSUE_NUMBER="$1"
ISSUE_TYPE="${2:-feature}"  # Default to feature if not specified
BRANCH_NAME=""

# Fetch issue details using GitHub CLI directly
echo "Fetching issue details for #$ISSUE_NUMBER..."
ISSUE_JSON=$(gh issue view "$ISSUE_NUMBER" --json number,title)
if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch issue #$ISSUE_NUMBER. Make sure the issue exists and gh is properly configured."
    exit 1
fi

# Extract the issue title using jq
ISSUE_TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')

if [ -z "$ISSUE_TITLE" ]; then
    echo "Error: Could not extract issue title. Make sure issue #$ISSUE_NUMBER exists."
    exit 1
fi

# Generate a slug from the issue title
SLUG=$(echo "$ISSUE_TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | cut -c 1-45)

# Create the branch name
BRANCH_NAME="${ISSUE_TYPE}/${ISSUE_NUMBER}-${SLUG}"

echo "Issue #$ISSUE_NUMBER: $ISSUE_TITLE"
echo "Issue type: $ISSUE_TYPE"
echo "Branch name: $BRANCH_NAME"

# Check if we're on the dev branch, if not switch automatically
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "dev" ]; then
    echo "Currently on branch '$CURRENT_BRANCH', switching to 'dev'..."
    git checkout dev
    if [ $? -ne 0 ]; then
        echo "Error: Failed to switch to dev branch. Branch might be dirty."
        echo "Git status:"
        git status
        exit 1
    fi
fi

# Make sure dev branch is up to date
echo "Updating dev branch..."
git pull origin dev
if [ $? -ne 0 ]; then
    echo "Error: Failed to update dev branch. There might be conflicts."
    echo "Git status:"
    git status
    exit 1
fi

# Check if branch already exists (locally or remotely)
echo "Checking if branch already exists..."
LOCAL_BRANCH_EXISTS=$(git branch --list "$BRANCH_NAME")
REMOTE_BRANCH_EXISTS=$(git ls-remote --heads origin "$BRANCH_NAME" | wc -l)

# Check for branches with the issue number (to catch issue-34 vs issue-334 confusion)
SIMILAR_BRANCHES=$(git branch -a | grep -E "/${ISSUE_NUMBER}-" | grep -v "$BRANCH_NAME")

if [ -n "$LOCAL_BRANCH_EXISTS" ] || [ "$REMOTE_BRANCH_EXISTS" -gt 0 ]; then
    echo "Warning: Branch '$BRANCH_NAME' already exists."
    echo "Switching to existing branch..."
    git checkout "$BRANCH_NAME"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to switch to existing branch '$BRANCH_NAME'."
        echo "Git status:"
        git status
        exit 1
    fi
elif [ -n "$SIMILAR_BRANCHES" ]; then
    echo "Warning: Found branches with similar issue number:"
    echo "$SIMILAR_BRANCHES"
    
    # Create the branch
    echo "Creating branch: $BRANCH_NAME"
    git checkout -b "$BRANCH_NAME"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create branch '$BRANCH_NAME'."
        echo "Git status:"
        git status
        exit 1
    fi
else
    # Create the branch
    echo "Creating branch: $BRANCH_NAME"
    git checkout -b "$BRANCH_NAME"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create branch '$BRANCH_NAME'."
        echo "Git status:"
        git status
        exit 1
    fi
fi

# Push the branch to origin
echo "Pushing branch to origin..."
git push --set-upstream origin "$BRANCH_NAME"
if [ $? -ne 0 ]; then
    echo "Error: Failed to push branch to origin."
    echo "Git status:"
    git status
    exit 1
fi

# Update current_issue.md
echo "Updating current issue information..."
mkdir -p "$PROJECT_ROOT/.vmpilot/prompts"
ISSUE_DETAILS=$(gh issue view "$ISSUE_NUMBER")
cat > "$PROJECT_ROOT/.vmpilot/prompts/current_issue.md" << EOF
# Current Issue: #$ISSUE_NUMBER - $ISSUE_TITLE

## Branch
\`\`\`
$BRANCH_NAME
\`\`\`

## Issue Details
\`\`\`
$ISSUE_DETAILS
\`\`\`
EOF

echo ""
echo "✅ Successfully created and pushed branch: $BRANCH_NAME"
echo "✅ Updated current issue information in .vmpilot/prompts/current_issue.md"
echo ""
echo "You are now working on issue #$ISSUE_NUMBER"
