#!/bin/bash
# new_chat.sh - Runs on a new chat.
# Currently fetches information about the current issue
# This script:
# 1. Detects the current git branch
# 2. Extracts the issue number from the branch name
# 3. Fetches the issue details using the github_issues plugin
# 4. Outputs the issue in markdown format

set -e

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")}"
GH_ISSUE_SCRIPT="${PROJECT_ROOT}/src/vmpilot/plugins/github_issues/gh_issue.sh"

# Function to detect current branch and extract issue number
get_issue_number() {
  # Get current branch name
  local branch=$(git branch --show-current 2>/dev/null)
  
  if [ -z "$branch" ]; then
    echo "Not in a git repository or no current branch." >&2
    return 1
  fi
  
  # Extract issue number from branch name (assumes format contains the issue number)
  # Examples: feature/123-description, 123-fix-bug, issue-123, etc.
  local issue_number=$(echo "$branch" | grep -oE '[0-9]+' | head -1)
  
  if [ -z "$issue_number" ]; then
    echo "Could not extract issue number from branch: $branch" >&2
    return 1
  fi
  
  echo "$issue_number"
}

# Function to create markdown output with issue and branch info
format_issue_output() {
  local issue_number="$1"
  local branch="$2"
  local issue_content="$3"
  
  # Create markdown header
  echo "# Current Issue: #$issue_number"
  echo ""
  echo "## Branch"
  echo "\`\`\`"
  echo "$branch"
  echo "\`\`\`"
  echo ""
  echo "## Issue Details"
  echo "\`\`\`"
  echo "$issue_content"
  echo "\`\`\`"
}

# Main execution
main() {
  # Try to get issue number from branch
  local issue_number=$(get_issue_number)
  local exit_code=$?
  
  # If issue number extraction failed, exit with error
  if [ $exit_code -ne 0 ]; then
    echo "# No Current Issue Detected"
    echo ""
    echo "Could not detect a current issue from the git branch."
    echo "If you're working on a specific issue, consider naming your branch with the issue number."
    exit 0
  fi
  
  # Get current branch for reference
  local branch=$(git branch --show-current)
  
  # Fetch issue details using gh_issue.sh
  if [ -f "$GH_ISSUE_SCRIPT" ]; then
    local issue_content=$("$GH_ISSUE_SCRIPT" view "$issue_number")
    format_issue_output "$issue_number" "$branch" "$issue_content"
  else
    echo "Error: GitHub issue script not found at $GH_ISSUE_SCRIPT" >&2
    exit 1
  fi
}

# Run the main function
main
