#!/bin/bash
# Test script for Google's Gemini models
# This test verifies VMPilot functionality with Google's Gemini models

# Exit on any error
set -e

# Check if TEST_DIR is set
if [ -z "$TEST_DIR" ]; then
    echo "ERROR: TEST_DIR environment variable not set"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the root directory of the project
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Process arguments for provider
PROVIDER="google"
MODEL="gemini-2.5-pro-preview-03-25"  # Default model
while getopts "p:m:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
    m) MODEL="$OPTARG" ;;
  esac
done

# Create a test file
TEST_FILE="$TEST_DIR/gemini_test.txt"
echo "This is a test file for Google Gemini model testing." > "$TEST_FILE"

echo "Testing Google Gemini model: $MODEL"
echo "Running simple question test..."

# Run a simple question through the CLI
OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -t 0 -p "$PROVIDER" 'What is the capital of France? Answer in one word only.')

# Validate the output
if [[ "$OUTPUT" != *"Paris"* ]]; then
    echo "ERROR: Output does not contain expected result 'Paris'"
    echo "Output: $OUTPUT"
    exit 1
fi

echo "Simple question test passed!"

# Test file modification capability
echo "Testing file modification..."
OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -t 0 -p "$PROVIDER" "Change 'test file' to 'evaluation file' in $TEST_FILE")

# Verify the change
if grep -q "This is a evaluation file for Google Gemini model testing." "$TEST_FILE"; then
    echo "File modification test passed!"
else
    echo "ERROR: Expected modification not found in file"
    echo "Current content:"
    cat "$TEST_FILE"
    exit 1
fi

# Test multi-turn conversation capability
echo "Testing multi-turn conversation..."

# First turn
OUTPUT=$("$SCRIPT_DIR/run_cli.sh" -t 0 -p "$PROVIDER" "List three programming languages.")

# Verify first response contains programming languages
if [[ "$OUTPUT" != *"Python"* && "$OUTPUT" != *"Java"* && "$OUTPUT" != *"JavaScript"* && "$OUTPUT" != *"C++"* && "$OUTPUT" != *"C#"* && "$OUTPUT" != *"Ruby"* && "$OUTPUT" != *"Go"* && "$OUTPUT" != *"Rust"* ]]; then
    echo "ERROR: First response does not contain any expected programming languages"
    echo "Output: $OUTPUT"
    exit 1
fi

echo "Multi-turn conversation test passed!"

echo "All Google Gemini tests passed! ✅"
exit 0
