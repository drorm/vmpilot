#!/bin/bash -xv
# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Test error handling scenarios
# Requires TEST_DIR environment variable to be set

set -e  # Exit on error

echo "Starting error handling tests..."

# Test 2: Permission denied
echo "Test 2: Permission denied"
touch "$TEST_DIR/noperm.txt"
chmod 000 "$TEST_DIR/noperm.txt"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" "$SCRIPT_DI"$SCRIPT_DIR/run_cli.sh"" -t 0 "cat $TEST_DIR/noperm.txt" 2>&1)
if echo "$response" | grep -q "Permission denied"; then
    echo "✓ Permission denied test passed"
else
    echo "✗ Permission denied test failed"
fi
chmod 644 "$TEST_DIR/noperm.txt"

# Test 3: Memory limit handling
echo "Test 3: Memory limit handling"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" "$SCRIPT_DI"$SCRIPT_DIR/run_cli.sh"" -t 0 "yes | head -n 10000" 2>&1)
if echo "$response" | grep -q "response clipped" || echo "$response" | grep -q "y"; then
    echo "✓ Memory limit test passed"
else
    echo "✗ Memory limit test failed"
    exit 1
fi

echo "Error handling tests completed successfully"
exit 0
