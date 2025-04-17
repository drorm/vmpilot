#!/bin/bash
# Script to view GitHub issues with proper handling of issues that have no comments
# Usage: ./view_issue.sh <issue_number>

set -e

if [ -z "$1" ]; then
  echo "Error: Issue number is required"
  echo "Usage: ./view_issue.sh <issue_number>"
  exit 1
fi

ISSUE_NUMBER=$1
PROJECT_ROOT="/home/dror/vmpilot"
cd "$PROJECT_ROOT" || exit 1

# First get the issue details with JSON to check if there are comments
ISSUE_JSON=$(gh issue view "$ISSUE_NUMBER" --json number,title,body,comments)

# Extract comment count using jq if available, or fallback to grep and wc
if command -v jq &> /dev/null; then
  COMMENT_COUNT=$(echo "$ISSUE_JSON" | jq '.comments | length')
else
  # Fallback for systems without jq
  COMMENT_COUNT=$(echo "$ISSUE_JSON" | grep -o '"comments":\[[^]]*\]' | grep -o '{' | wc -l)
fi

# First display the issue content without comments
ISSUE_CONTENT=$(gh issue view "$ISSUE_NUMBER")
echo "$ISSUE_CONTENT"

# Then handle comments separately
if [ "$COMMENT_COUNT" -gt 0 ]; then
  echo -e "\n----- COMMENTS -----"
  # Use JSON to reliably get comments
  if command -v jq &> /dev/null; then
    echo "$ISSUE_JSON" | jq -r '.comments[] | "Author: \(.author.login)\nDate: \(.createdAt)\n\n\(.body)\n---"'
  else
    # Fallback if jq is not available - use the gh comments output
    COMMENTS_OUTPUT=$(gh issue view "$ISSUE_NUMBER" --comments)
    # Extract only the comments part (everything after the first "--" line)
    echo "$COMMENTS_OUTPUT" | sed -n '/^--$/,$p'
  fi
else
  echo -e "\n----- NO COMMENTS -----"
fi
