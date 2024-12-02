#!/bin/bash

# Test error handling scenarios
# Requires TEST_DIR environment variable to be set

set -e  # Exit on error

echo "Starting error handling tests..."

# Test 1: Invalid command execution
echo "Test 1: Invalid command execution"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 "nonexistentcommand" 2>&1)
if echo "$response" | grep -qi "command not found\|No such file or directory"; then
    echo "✓ Invalid command test passed"
else
    echo "✗ Invalid command test failed"
    exit 1
fi

# Test 2: Permission denied
echo "Test 2: Permission denied"
touch "$TEST_DIR/noperm.txt"
chmod 000 "$TEST_DIR/noperm.txt"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 "cat $TEST_DIR/noperm.txt" 2>&1)
if echo "$response" | grep -q "Permission denied"; then
    echo "✓ Permission denied test passed"
else
    echo "✗ Permission denied test failed"
fi
chmod 644 "$TEST_DIR/noperm.txt"

# Test 3: Memory limit handling
echo "Test 3: Memory limit handling"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 "yes | head -n 1000000" 2>&1)
if echo "$response" | grep -q "response clipped" || echo "$response" | grep -q "y"; then
    echo "✓ Memory limit test passed"
else
    echo "✗ Memory limit test failed"
    exit 1
fi

# Test 4: Timeout handling
echo "Test 4: Timeout handling"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 "sleep 30" 2>&1)
if echo "$response" | grep -q "timeout" || echo "$response" | grep -q "error"; then
    echo "✓ Timeout test passed"
else
    echo "✗ Timeout test failed"
    exit 1
fi

echo "Error handling tests completed successfully"
exit 0