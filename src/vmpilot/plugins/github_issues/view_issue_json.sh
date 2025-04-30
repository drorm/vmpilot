#!/bin/bash
# Script to view GitHub issues using JSON output for consistent results
# Usage: ./view_issue_json.sh <issue_number>

set -e

if [ -z "$1" ]; then
  echo "Error: Issue number is required"
  echo "Usage: ./view_issue_json.sh <issue_number>"
  exit 1
fi

ISSUE_NUMBER=$1
PROJECT_ROOT="/home/dror/vmpilot"
cd "$PROJECT_ROOT" || exit 1

# Get the issue details with JSON
ISSUE_JSON=$(gh issue view "$ISSUE_NUMBER" --json number,title,body,state,author,createdAt,comments,labels,assignees)

# Format the output in a readable way
echo "Issue #$(echo "$ISSUE_JSON" | jq -r '.number'): $(echo "$ISSUE_JSON" | jq -r '.title')"
echo "State: $(echo "$ISSUE_JSON" | jq -r '.state')"
echo "Author: $(echo "$ISSUE_JSON" | jq -r '.author.login')"
echo "Created: $(echo "$ISSUE_JSON" | jq -r '.createdAt')"
echo "Labels: $(echo "$ISSUE_JSON" | jq -r '.labels[].name' | tr '\n' ', ' | sed 's/,$//' | sed 's/, $//')"

echo -e "\n----- DESCRIPTION -----"
echo "$ISSUE_JSON" | jq -r '.body'

COMMENT_COUNT=$(echo "$ISSUE_JSON" | jq '.comments | length')

if [ "$COMMENT_COUNT" -gt 0 ]; then
  echo -e "\n----- COMMENTS ($COMMENT_COUNT) -----"
  echo "$ISSUE_JSON" | jq -r '.comments[] | "Author: \(.author.login)\nDate: \(.createdAt)\n\n\(.body)\n---"'
else
  echo -e "\n----- NO COMMENTS -----"
fi