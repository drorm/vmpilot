#!/bin/bash

# Test API integration and responses
# Requires TEST_DIR environment variable to be set

set -e  # Exit on error

echo "Starting API integration tests..."

# Test 1: Check API key validation
echo "Test 1: API key validation"
response=$(ANTHROPIC_API_KEY="invalid_key" ../bin/cli.sh -t 0 "echo test" 2>&1)
if echo "$response" | grep -q "Error: Invalid or missing API key"; then
    echo "✓ Invalid API key test passed"
else
    echo "✗ Invalid API key test failed"
    echo "Response was: $response"
    exit 1
fi

# Test 2: Basic API connectivity
echo "Test 2: Basic API connectivity"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 "echo 'hello world'" 2>&1)
if echo "$response" | grep -q "hello world"; then
    echo "✓ Basic API connectivity test passed"
else
    echo "✗ Basic API connectivity test failed"
    exit 1
fi

# Test 3: Model selection
echo "Test 3: Model selection"
if ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" MODEL_ID="invalid-model" ../bin/cli.sh -t 0 "echo test" 2>&1 | grep -q "Unsupported model"; then
    echo "✓ Model selection test passed"
else
    echo "✗ Model selection test failed"
    exit 1
fi

# Test 4: Response formatting
echo "Test 4: Response formatting"
response=$(ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" ../bin/cli.sh -t 0 "ls -l" 2>&1)
if echo "$response" | grep -q "\`\`\`plain"; then
    echo "✓ Response formatting test passed"
else
    echo "✗ Response formatting test failed"
    exit 1
fi

echo "API integration tests completed successfully"
exit 0