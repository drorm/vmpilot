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

echo "Running chat end-to-end test..."

# Create a temporary directory for this specific test
TEST_TEMP_DIR=$(mktemp -d)
echo "Created temporary test directory: $TEST_TEMP_DIR"

# Setup the test environment as specified
PYTHON_FILE="$TEST_TEMP_DIR/5V0I.py"
echo 'print("Hello World")' > "$PYTHON_FILE"
echo "Created test Python file: $PYTHON_FILE"

# Test the first part of the conversation
echo "Testing first chat interaction..."
output1=$(../bin/cli.sh -p "$PROVIDER" -t 0 "Show me the files in $TEST_TEMP_DIR")

# Verify the first response contains the expected information
if echo "$output1" | grep -q "5V0I.py" && echo "$output1" | grep -q -i "python"; then
    echo "✅ First chat interaction passed"
else
    echo "❌ First chat interaction failed"
    echo "Got output:"
    echo "$output1"
    echo "Expected output to mention 5V0I.py and identify it as a Python file"
    rm -rf "$TEST_TEMP_DIR"
    exit 1
fi

# Test the second part of the conversation
echo "Testing second chat interaction..."

# Extract the chat_id from the first response
chat_id=$(echo "$output1" | head -n1 | grep -oP 'Chat id:\s*\K[^\s]+')
if [ -z "$chat_id" ]; then
    echo "❌ Failed to extract chat_id from first response"
    echo "First response was:"
    echo "$output1"
    rm -rf "$TEST_TEMP_DIR"
    exit 1
fi
echo "Extracted chat_id: $chat_id"


# Use the -c flag with the extracted chat_id to continue the conversation
output2=$(../bin/cli.sh -p "$PROVIDER" -t 0 -c "$chat_id" "Show me the contents of the file and also run it")

# Verify the second response contains the expected information
if echo "$output2" | grep -q "Hello World" && echo "$output2" | grep -q "print"; then
    echo "✅ Second chat interaction passed"
else
    echo "❌ Second chat interaction failed"
    echo "Got output:"
    echo "$output2"
    echo "Expected output to show the file contents (print statement) and execution result (Hello World)"
    rm -rf "$TEST_TEMP_DIR"
    exit 1
fi

# Clean up
rm -rf "$TEST_TEMP_DIR"
echo "✅ Chat end-to-end test passed"
exit 0
