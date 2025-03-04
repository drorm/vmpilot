#!/bin/bash

# Test API integration and responses
# Requires TEST_DIR environment variable to be set

set -e  # Exit on error

# Set the absolute path to cli.sh
CLI_PATH="/home/dror/vmpilot/bin/cli.sh"

echo "Starting API integration tests..."

# Test 1: Check API key validation
echo "Test 1: API key validation"
response=$(ANTHROPIC_API_KEY="invalid_key" $CLI_PATH -t 0 "echo test" 2>&1)
if echo "$response" | grep -q -i "Error: Invalid or missing Anthropic API key"; then
    echo "✓ Invalid API key test passed"
else
    echo "✗ Invalid API key test failed"
    echo "Response was: $response"
    exit 1
fi

# Ensure ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY environment variable is not set"
    exit 1
fi

# Test 2: Basic API connectivity
echo "Test 2: Basic API connectivity"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" $CLI_PATH -t 0 "echo 'hello world'" 2>&1)
if echo "$response" | grep -q "hello world"; then
    echo "✓ Basic API connectivity test passed"
else
    echo "✗ Basic API connectivity test failed"
    exit 1
fi

# Test 3: Model selection with explicit model
echo "Test 3: Model selection with explicit model"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" $CLI_PATH -t 0 -m "claude-3-sonnet-20240229" "echo test" 2>&1)
if echo "$response" | grep -q "test"; then
    echo "✓ Model selection test passed"
else
    echo "✗ Model selection test failed"
    exit 1
fi

# Test 4: Response formatting
echo "Test 4: Response formatting"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" $CLI_PATH -t 0 "ls -l" 2>&1)
if echo "$response" | grep -q "\`\`\`"; then
    echo "✓ Response formatting test passed"
else
    echo "✗ Response formatting test failed"
    exit 1
fi

echo "API integration tests completed successfully"
exit 0
