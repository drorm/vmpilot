#!/bin/bash
# Test for conversation persistence using chat IDs
# This test verifies that the SQLite persistence feature (Issue #31) is working correctly
# by ensuring a conversation can be continued using a chat ID across multiple commands

# Exit on any error
set -e

# Process arguments for provider
PROVIDER="anthropic"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done
shift $((OPTIND -1))

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the root directory of the project
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================================"
echo "Testing SQLite conversation persistence with chat IDs..."
echo "========================================================"

# Step 1: Run the first command and extract the chat ID
echo -e "\n[Step 1] Getting first 3 lines of README.md..."
FIRST_OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -p "$PROVIDER" -t 0 "show me the first 3 lines in $PROJECT_ROOT/README.md")

# Extract the chat ID from the output
CHAT_ID=$(echo "$FIRST_OUTPUT" | grep -o "Chat id :[0-9a-zA-Z]\+" | sed 's/Chat id ://')

if [ -z "$CHAT_ID" ]; then
    echo "ERROR: Could not extract chat ID from output"
    echo "Output was:"
    echo "$FIRST_OUTPUT"
    exit 1
fi

echo -e "Successfully extracted chat ID: \033[1;32m$CHAT_ID\033[0m"

# Validate first output has expected content
if [[ "$FIRST_OUTPUT" != *"VMPilot"* || "$FIRST_OUTPUT" != *"chat-based AI development agent"* ]]; then
    echo -e "\033[1;31mERROR:\033[0m First output does not contain expected content from README.md"
    echo -e "Expected to find 'VMPilot' and 'chat-based AI development agent'"
    echo -e "Output was:\n$FIRST_OUTPUT"
    exit 1
fi

echo -e "\033[1;32m✓\033[0m First command validated successfully"

# Step 2: Continue the conversation using the chat ID
echo -e "\n[Step 2] Getting the next 3 lines using chat ID $CHAT_ID..."
SECOND_OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -p "$PROVIDER" -t 0 -c "$CHAT_ID" "show me the next 3")

# Validate second output shows awareness of the previous context
if [[ "$SECOND_OUTPUT" != *"next 3 lines"* ]]; then
    echo -e "\033[1;31mERROR:\033[0m Second output does not show context awareness"
    echo -e "Expected to find reference to 'next 3 lines'"
    echo -e "Output was:\n$SECOND_OUTPUT"
    exit 1
fi

# Check if it contains content from lines 4-6 (likely the image reference)
if [[ "$SECOND_OUTPUT" != *"hello"* && "$SECOND_OUTPUT" != *".png"* ]]; then
    echo -e "\033[1;31mERROR:\033[0m Second output does not contain expected content from README.md"
    echo -e "Expected to find content from lines 4-6"
    echo -e "Output was:\n$SECOND_OUTPUT"
    exit 1
fi

echo -e "\033[1;32m✓\033[0m Second command validated successfully"

# Step 3: Verify persistence by simulating a restart - use the same chat ID again
echo -e "\n[Step 3] Simulating application restart by using the same chat ID again..."
THIRD_OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -p "$PROVIDER" -t 0 -c "$CHAT_ID" "summarize our conversation so far")

# Check if the summary references both previous interactions
if [[ "$THIRD_OUTPUT" != *"first 3 lines"* || "$THIRD_OUTPUT" != *"next 3"* ]]; then
    echo -e "\033[1;31mERROR:\033[0m Third output does not show persistence across the full conversation"
    echo -e "Expected summary to reference both previous commands"
    echo -e "Output was:\n$THIRD_OUTPUT"
    exit 1
fi

echo -e "\033[1;32m✓\033[0m Third command validated successfully"

echo -e "\n\033[1;32m==========================================\033[0m"
echo -e "\033[1;32mTest passed! SQLite conversation persistence using chat IDs is working correctly.\033[0m"
echo -e "\033[1;32m==========================================\033[0m"
exit 0
