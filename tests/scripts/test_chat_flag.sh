#!/bin/bash
#
# Test script for the --chat flag feature (Issue #33)
# This script tests the ability to maintain conversation context across multiple CLI invocations
# and the file input feature (-f/--file flag)
#

# Enable error handling
set -e

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"
CLI_PATH="$PROJECT_ROOT/bin/cli.sh"

# Create a temporary directory for test outputs
TEST_DIR=$(mktemp -d)
echo "Creating temporary test directory: $TEST_DIR"

# Generate a unique chat ID for testing
CHAT_ID="test_chat_$(date +%s)"
echo "Using chat ID: $CHAT_ID"

# Function to run a command and capture output
run_command() {
    local prompt="$1"
    local output_file="$2"
    local chat_flag="$3"
    
    echo -e "\n>>> Running command: $prompt"
    if [ -n "$chat_flag" ]; then
        $CLI_PATH --chat "$chat_flag" "$prompt" > "$output_file" 2>&1
        # $CLI_PATH --chat "$chat_flag" "$prompt" | tee > "$output_file" 2>&1
    else
        $CLI_PATH "$prompt" > "$output_file" 2>&1
    fi
    echo "Output saved to: $output_file"
    echo "--- Command output preview ---"
    head -n 5 "$output_file"
    if [ "$(wc -l < "$output_file")" -gt 5 ]; then
        echo "... (output truncated) ..."
    fi
    echo "-----------------------------"
}

# Test 1: Basic functionality with --chat flag
echo "=== Test 1: Basic functionality with --chat flag ==="
run_command "What is the current working directory?" "$TEST_DIR/test1_output.txt" "$CHAT_ID"

# Test 2: Verify context is maintained (referencing the sample files directory)
echo "=== Test 2: Verify context is maintained ==="
run_command "What files are in the tests/sample_files directory?" "$TEST_DIR/test2_output.txt" "$CHAT_ID"

# Test 3: Continuing the conversation with further context about a specific file
echo "=== Test 3: Continuing the conversation ==="
run_command "What is the content of the test2.py file you found in that directory?" "$TEST_DIR/test3_output.txt" "$CHAT_ID"

# Test 4: Verify a new chat ID creates a separate conversation
echo "=== Test 4: New chat ID creates separate conversation ==="
NEW_CHAT_ID="test_chat_new_$(date +%s)"
run_command "What files did we discuss in our previous conversation?" "$TEST_DIR/test4_output.txt" "$NEW_CHAT_ID"

# Test 5: Compare with no chat flag (should not have context)
echo "=== Test 5: No chat flag should not have context ==="
run_command "What directory were we talking about earlier?" "$TEST_DIR/test5_output.txt"

# Function to check if the output contains expected content
check_output() {
    local file="$1"
    local pattern="$2"
    local test_name="$3"
    
    if grep -q "$pattern" "$file"; then
        echo "✅ $test_name: PASSED - Found expected content"
    else
        echo "❌ $test_name: FAILED - Expected content not found"
        echo "Expected to find: '$pattern'"
        echo "File content:"
        cat "$file"
    fi
}

# Perform validation checks
echo -e "\n=== Validation Checks ==="

# Check Test 2 - Should list files in sample_files directory
check_output "$TEST_DIR/test2_output.txt" "test1\.txt|test2\.py|test_commands\.txt" "Context Maintenance Test"

# Check Test 3 - Should show content of test2.py
check_output "$TEST_DIR/test3_output.txt" "sample_function|print|This is a sample Python file" "Extended Context Test"

# Check Test 4 - Should NOT have context from the first chat session
check_output "$TEST_DIR/test4_output.txt" "previous|don't know|new conversation" "Separate Chat Test"

# Check Test 5 - Should NOT have context without chat flag
check_output "$TEST_DIR/test5_output.txt" "don't know|no previous|not sure" "No Chat Flag Test"

# Test 6: Test file input feature with chat context
echo -e "\n=== Test 6: File Input Feature with Chat Context ==="
echo "Running commands from file with chat context..."
$CLI_PATH -f "$PROJECT_ROOT/tests/sample_files/test_commands.txt" --chat "$CHAT_ID" > "$TEST_DIR/test6_output.txt" 2>&1
echo "Output saved to: $TEST_DIR/test6_output.txt"

# Check Test 6 - Should execute all commands in the file with chat context
check_output "$TEST_DIR/test6_output.txt" "Executing command.*ls -la" "File Input Test"

# Summary
echo -e "\n=== Test Summary ==="
echo "Tests completed. Review the outputs in: $TEST_DIR"
echo "Chat ID used: $CHAT_ID"
echo "New Chat ID used: $NEW_CHAT_ID"

# Cleanup instructions
echo -e "\nTo clean up test files, run: rm -rf $TEST_DIR"
