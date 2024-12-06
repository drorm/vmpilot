#!/bin/bash

# Setup
TEST_DIR=$(mktemp -d)
echo "Creating test environment in $TEST_DIR"

# Copy sample files to test directory
cp -r tests/sample_files/* "$TEST_DIR/" 2>/dev/null || true

# Export test directory for test scripts
export TEST_DIR

# Run tests
echo "Running tests..."

if [ $# -eq 0 ]; then
    # If no arguments provided, run all tests
    test_files=(scripts/*.sh)
else
    # If arguments provided, use them as test files
    test_files=("$@")
fi

for test in "${test_files[@]}"; do
    if [ ! -f "$test" ]; then
        echo "❌ Test file not found: $test"
        failed_tests=1
        continue
    fi
    
    echo "Running $test..."
    if bash "$test"; then
        echo "✅ $test passed"
    else
        echo "❌ $test failed"
        failed_tests=1
    fi
    echo "-------------------"
done

# Cleanup
echo "Cleaning up test environment..."
rm -rf "$TEST_DIR"

# Exit with status
if [ -n "$failed_tests" ]; then
    exit 1
else
    echo "All tests passed! 🎉"
    exit 0
fi