#!/bin/bash
# Test script for code retrieval to find SQLite default path without looking at files directly

# Exit on any error
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Check if TEST_DIR is set
if [ -z "$TEST_DIR" ]; then
    echo "ERROR: TEST_DIR environment variable not set"
    exit 1
fi

cd "$TEST_DIR"

# Process arguments for provider
PROVIDER="anthropic"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done

# Ensure code index exists for the actual project
if [ ! -d "$HOME/.vmpilot/code_index" ]; then
    echo "Building code index for the project..."
    "$/bin/build_code_index.sh" --source "$SCRIPT_DIR"
    
    # Check if the index was created
    if [ ! -d "$HOME/.vmpilot/code_index" ]; then
        echo "ERROR: Code index could not be created"
        exit 1
    fi
fi

# Test the CLI with code retrieval to find SQLite default path
echo "Testing code retrieval for SQLite default path..."
CLI_OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -t 0 -p "$PROVIDER" "use the code retrieval tool, but don't look at any files directly. Find out the default path the sqlite db. Tell me the results, and nothing else")

# Validate the CLI output for specific expected content
if [[ "$CLI_OUTPUT" != *"~/.vmpilot/vmpilot.db"* ]]; then
    echo "ERROR: CLI query didn't return expected home directory path (~/.vmpilot/vmpilot.db)"
    echo "Output: $CLI_OUTPUT"
    exit 1
fi

if [[ "$CLI_OUTPUT" != *"/app/data/vmpilot.db"* ]]; then
    echo "ERROR: CLI query didn't return expected Docker path (/app/data/vmpilot.db)"
    echo "Output: $CLI_OUTPUT"
    exit 1
fi

if [[ "$CLI_OUTPUT" != *"get_db_path"* ]]; then
    echo "ERROR: CLI query didn't mention the get_db_path function"
    echo "Output: $CLI_OUTPUT"
    exit 1
fi

# Test that the tool didn't directly look at files (no direct file access commands should be in output)
if [[ "$CLI_OUTPUT" == *"cat "* ]] || [[ "$CLI_OUTPUT" == *"head "* ]] || [[ "$CLI_OUTPUT" == *"tail "* ]] || [[ "$CLI_OUTPUT" == *"less "* ]]; then
    echo "ERROR: The response shows direct file access commands were used"
    echo "Output: $CLI_OUTPUT"
    exit 1
fi

echo "Test passed successfully!"
exit 0
