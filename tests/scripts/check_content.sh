#!/bin/bash

# Exit on any error
set -e

# Default provider
PROVIDER="openai"

# Parse command-line options
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done
shift $((OPTIND -1))

# TEST_DIR should be set by harness.sh
if [ -z "$TEST_DIR" ]; then
    echo "Error: TEST_DIR not set"
    exit 1
fi

# Copy our test file to the temp directory
cp sample_files/test2.py "$TEST_DIR/"

echo "Running content check test..."

# Run the CLI command with temperature 0 for consistency
output=$(../bin/cli.sh -p "$PROVIDER" -t 0 "What does the Python file $TEST_DIR/test2.py do? Be concise.")

# Expected output - we'll use grep to look for key terms that should be present
if echo "$output" | grep -q "sample" && echo "$output" | grep -q "function" && echo "$output" | grep -q "print"; then
    echo "✅ Content check test passed"
    exit 0
else
    echo "❌ Content check test failed"
    echo "Got output:"
    echo "$output"
    echo "Expected output to contain description of a sample function that prints"
    exit 1
fi
