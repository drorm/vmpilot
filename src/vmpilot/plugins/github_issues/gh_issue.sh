#!/bin/bash
# Main entry point for GitHub issue operations
# Handles viewing, listing, creating, closing, and reopening issues

set -e

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/dror/vmpilot"

# Help function
show_help() {
  echo "GitHub Issue Management Script"
  echo "------------------------------"
  echo "Usage: ./gh_issue.sh [command] [options]"
  echo ""
  echo "Commands:"
  echo "  view <number>       View an issue (handles no-comments case)"
  echo "  view-json <number>  View issue in JSON format"
  echo "  list                List all open issues"
  echo "  create [options]    Create a new issue"
  echo "  close <number>      Close an issue"
  echo "  reopen <number>     Reopen a closed issue"
  echo ""
  echo "Examples:"
  echo "  ./gh_issue.sh view 10"
  echo "  ./gh_issue.sh list"
  echo "  ./gh_issue.sh create --title \"New Feature\" --label \"enhancement\""
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
  show_help
  exit 1
fi

# Process commands
COMMAND=$1
shift

case "$COMMAND" in
  view)
    if [ -z "$1" ]; then
      echo "Error: Issue number is required"
      echo "Usage: ./gh_issue.sh view <number>"
      exit 1
    fi
    "$SCRIPT_DIR/view_issue.sh" "$1"
    ;;
  
  view-json)
    if [ -z "$1" ]; then
      echo "Error: Issue number is required"
      echo "Usage: ./gh_issue.sh view-json <number>"
      exit 1
    fi
    "$SCRIPT_DIR/view_issue_json.sh" "$1"
    ;;
  
  list)
    cd "$PROJECT_ROOT" && gh issue list "$@"
    ;;
  
  create)
    cd "$PROJECT_ROOT" && gh issue create "$@"
    ;;
  
  close)
    if [ -z "$1" ]; then
      echo "Error: Issue number is required"
      echo "Usage: ./gh_issue.sh close <number>"
      exit 1
    fi
    cd "$PROJECT_ROOT" && gh issue close "$1"
    ;;
  
  reopen)
    if [ -z "$1" ]; then
      echo "Error: Issue number is required"
      echo "Usage: ./gh_issue.sh reopen <number>"
      exit 1
    fi
    cd "$PROJECT_ROOT" && gh issue reopen "$1"
    ;;
  
  help|--help|-h)
    show_help
    ;;
  
  *)
    echo "Error: Unknown command '$COMMAND'"
    show_help
    exit 1
    ;;
esac