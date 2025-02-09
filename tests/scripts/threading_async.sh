#!/bin/bash

# Test concurrent operations and threading behavior
# Requires TEST_DIR environment variable to be set

set -e  # Exit on error

echo "Starting threading and async tests..."

# Test 1: Concurrent requests
echo "Test 1: Concurrent requests"
for i in {1..3}; do
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 "echo 'Request $i'" > "$TEST_DIR/output_$i.txt" 2>&1 &
done

# Wait for all background processes
wait
# Check all outputs exist and are valid
for i in {1..3}; do
    if grep -q "Request $i" "$TEST_DIR/output_$i.txt"; then
        echo "✓ Concurrent request $i completed successfully"
    else
        echo "✗ Concurrent request $i failed"
        exit 1
    fi
done

# Test 2: Background process handling
echo "Test 2: Background process handling"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 "sleep 5 & echo 'immediate'" 2>&1)
if echo "$response" | grep -q "immediate"; then
    echo "✓ Background process test passed"
else
    echo "✗ Background process test failed"
    exit 1
fi

# Test 3: Multiple command pipeline
echo "Test 3: Multiple command pipeline"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 "echo 'start' && sleep 2 && echo 'end'" 2>&1)
if echo "$response" | grep -q "start" && echo "$response" | grep -q "end"; then
    echo "✓ Multiple command pipeline test passed"
else
    echo "✗ Multiple command pipeline test failed"
    exit 1
fi

# Test 4: Stream mode with background tasks
# echo "Test 4: Stream mode with background tasks"
# response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 --stream "for i in {1..3}; do echo \$i & done" 2>&1)
# if echo "$response" | grep -q "1" && echo "$response" | grep -q "2" && echo "$response" | grep -q "3"; then
    # echo "✓ Stream mode with background tasks test passed"
# else
    # echo "✗ Stream mode with background tasks test failed"
    # exit 1
# fi

echo "Threading and async tests completed successfully"
exit 0
