#!/bin/bash

# Input: Issue title and number
read -p "Enter issue title:" ISSUE_TITLE

PROMPT="Generate a Git-compatible branch name from the following GitHub issue title. Start with a lowercase category like bug, feature, docs, or chore, etc. Include the issue number from the title. Use a short, hyphen-separated summary (truncate to 40 characters if necessary). Replace spaces with hyphens and convert to lowercase. Output only the branch name. Issue: $ISSUE_TITLE"

BRANCH_NAME=`gish -m gpt-4o --no-stats $PROMPT`

# Step 6: Confirm merge
read -p "Are you sure you want to create branch $BRANCH_NAME? [y/N] " confirm_create
if [[ ! $confirm_create =~ ^[Yy]$ ]]; then
    echo "Create branch aborted by user."
    exit 0
fi

echo "Creating branch: $BRANCH_NAME"

# Create the branch
git checkout -b "$BRANCH_NAME"

git push --set-upstream origin "$BRANCH_NAME"

# Output confirmation
echo "Branch created: $BRANCH_NAME"
