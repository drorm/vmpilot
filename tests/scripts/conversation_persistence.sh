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

# Create temporary files for the verbose output of each command
FIRST_OUTPUT_LOG=$(mktemp)
SECOND_OUTPUT_LOG=$(mktemp)
THIRD_OUTPUT_LOG=$(mktemp)
trap 'rm -f "$FIRST_OUTPUT_LOG" "$SECOND_OUTPUT_LOG" "$THIRD_OUTPUT_LOG"' EXIT

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the root directory of the project
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================================"
echo "Testing SQLite conversation persistence with chat IDs..."
echo "========================================================"

# Step 1: Run the first command and extract the chat ID
echo -e "\n[Step 1] Getting first 3 lines of README.md..."
FIRST_OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -p "$PROVIDER" -t 0 -v "show me the first 3 lines in $PROJECT_ROOT/README.md" 2>&1 | tee "$FIRST_OUTPUT_LOG")

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
SECOND_OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -p "$PROVIDER" -t 0 -v -c "$CHAT_ID" "show me the next 3" 2>&1 | tee "$SECOND_OUTPUT_LOG")

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
THIRD_OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -p "$PROVIDER" -t 0 -v -c "$CHAT_ID" "summarize our conversation so far" 2>&1 | tee "$THIRD_OUTPUT_LOG")

# Check if the summary references both previous interactions
if [[ "$THIRD_OUTPUT" != *"first 3 lines"* || "$THIRD_OUTPUT" != *"next 3"* ]]; then
    echo -e "\033[1;31mERROR:\033[0m Third output does not show persistence across the full conversation"
    echo -e "Expected summary to reference both previous commands"
    echo -e "Output was:\n$THIRD_OUTPUT"
    exit 1
fi

echo -e "\033[1;32m✓\033[0m Third command validated successfully"

# Step 4: Validate token usage and caching
echo -e "\n[Step 4] Validating token usage and caching effectiveness..."

# Extract token usage information from each log file
# Get the last TOKEN_USAGE entry from each log (in case there are multiple)
FIRST_TOKEN_USAGE=$(grep "TOKEN_USAGE" "$FIRST_OUTPUT_LOG" | tail -1)
SECOND_TOKEN_USAGE=$(grep "TOKEN_USAGE" "$SECOND_OUTPUT_LOG" | tail -1)
THIRD_TOKEN_USAGE=$(grep "TOKEN_USAGE" "$THIRD_OUTPUT_LOG" | tail -1)

# Check if we have token usage information for all commands
if [ -z "$FIRST_TOKEN_USAGE" ] || [ -z "$SECOND_TOKEN_USAGE" ] || [ -z "$THIRD_TOKEN_USAGE" ]; then
    echo -e "\033[1;31mERROR:\033[0m Missing token usage information"
    echo -e "First command token usage: $FIRST_TOKEN_USAGE"
    echo -e "Second command token usage: $SECOND_TOKEN_USAGE"
    echo -e "Third command token usage: $THIRD_TOKEN_USAGE"
    exit 1
fi

echo -e "Token usage entries:"
echo -e "First command: $FIRST_TOKEN_USAGE"
echo -e "Second command: $SECOND_TOKEN_USAGE"
echo -e "Third command: $THIRD_TOKEN_USAGE"

# Extract cache read tokens from the second command
SECOND_CACHE_READ=$(echo "$SECOND_TOKEN_USAGE" | grep -o "cache_read_input_tokens': [0-9]\+" | grep -o "[0-9]\+")
# Extract cache creation tokens from the second command
SECOND_CACHE_CREATION=$(echo "$SECOND_TOKEN_USAGE" | grep -o "cache_creation_input_tokens': [0-9]\+" | grep -o "[0-9]\+")

# Extract first command cache values for reference
FIRST_CACHE_READ=$(echo "$FIRST_TOKEN_USAGE" | grep -o "cache_read_input_tokens': [0-9]\+" | grep -o "[0-9]\+")
FIRST_CACHE_CREATION=$(echo "$FIRST_TOKEN_USAGE" | grep -o "cache_creation_input_tokens': [0-9]\+" | grep -o "[0-9]\+")

echo -e "\nCache token values:"
echo -e "First command - Cache read: $FIRST_CACHE_READ, Cache creation: $FIRST_CACHE_CREATION"
echo -e "Second command - Cache read: $SECOND_CACHE_READ, Cache creation: $SECOND_CACHE_CREATION"
echo -e "Third command - Cache read: $THIRD_CACHE_READ"

# Validation 1: Second command should have positive cache read tokens
# This verifies the first conversation is being cached and reused
if [ -z "$SECOND_CACHE_READ" ] || [ "$SECOND_CACHE_READ" -eq 0 ]; then
    echo -e "\033[1;31mERROR:\033[0m Cache read tokens not found in second command"
    echo -e "Expected positive value for cache_read_input_tokens"
    exit 1
fi

# Validation 2: Cache creation should be happening in the second command
# This verifies new content is being added to the cache
if [ -z "$SECOND_CACHE_CREATION" ] || [ "$SECOND_CACHE_CREATION" -eq 0 ]; then
    echo -e "\033[1;31mERROR:\033[0m Cache creation tokens not found in second command"
    echo -e "Expected positive value for cache_creation_input_tokens"
    exit 1
fi

# Extract cache read tokens from the third command
THIRD_CACHE_READ=$(echo "$THIRD_TOKEN_USAGE" | grep -o "cache_read_input_tokens': [0-9]\+" | grep -o "[0-9]\+")

# Validation 3: Third command should have positive cache read tokens
if [ -z "$THIRD_CACHE_READ" ] || [ "$THIRD_CACHE_READ" -eq 0 ]; then
    echo -e "\033[1;31mERROR:\033[0m Cache read tokens not found in third command"
    echo -e "Expected positive value for cache_read_input_tokens in third command"
    exit 1
fi

# Validation 4: Third command should have at least as many cache read tokens as second command
# This verifies that conversation history is being accumulated
# Note: In some cases they might be equal, which is acceptable
if [ "$THIRD_CACHE_READ" -lt "$SECOND_CACHE_READ" ]; then
    echo -e "\033[1;31mERROR:\033[0m Third command cache read tokens decreasing"
    echo -e "Expected third command cache_read_input_tokens ($THIRD_CACHE_READ) to be at least equal to second command ($SECOND_CACHE_READ)"
    exit 1
fi

# Calculate the percentage increase in cache read tokens
if [ -n "$THIRD_CACHE_READ" ] && [ -n "$SECOND_CACHE_READ" ] && [ "$SECOND_CACHE_READ" -gt 0 ]; then
    PERCENTAGE_INCREASE=$(( (THIRD_CACHE_READ - SECOND_CACHE_READ) * 100 / SECOND_CACHE_READ ))
    echo -e "Cache read tokens increased by approximately $PERCENTAGE_INCREASE% from second to third command"
fi
echo -e "Third command cache read tokens: \033[1;32m$THIRD_CACHE_READ\033[0m"

echo -e "Third command cache read tokens: \033[1;32m$THIRD_CACHE_READ\033[0m"
echo -e "\033[1;32m✓\033[0m Token usage validation successful"

echo -e "\n\033[1;32m==========================================\033[0m"
echo -e "\033[1;32mTest passed! Validation results:\033[0m"
echo -e "\033[1;32m1. SQLite conversation persistence is working correctly\033[0m"
echo -e "\033[1;32m2. Cache is being reused between commands\033[0m"
echo -e "\033[1;32m3. Cache is growing appropriately with conversation history\033[0m"
echo -e "\033[1;32m==========================================\033[0m"
exit 0
