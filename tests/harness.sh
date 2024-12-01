#!/bin/bash

# Setup
TEST_DIR=$(mktemp -d)
echo "Creating test environment in $TEST_DIR"

# Copy sample files to test directory
cp -r sample_files/* "$TEST_DIR/"

# Export test directory for test scripts
export TEST_DIR

# Run all test scripts
echo "Running tests..."
for test in scripts/*.sh; do
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