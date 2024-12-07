#!/bin/bash

# Setup
TEST_DIR=$(mktemp -d)
echo "Creating test environment in $TEST_DIR"
cd "$(dirname "$0")"


# Copy sample files to test directory
echo "Current working directory: $(pwd)"

cp -r /home/dror/vmpilot/tests/sample_files/* "$TEST_DIR/" 2>/dev/null || true

if [ $? -ne 0 ]; then echo "Error copying files to $TEST_DIR"; exit 1; fi
ls -l $TEST_DIR
# Explicitly check for the presence of the files in the test directory
if [ ! -f "$TEST_DIR/test1.txt" ] || [ ! -f "$TEST_DIR/test2.py" ]; then
    echo "Error: Test files not copied to $TEST_DIR"; exit 1
fi

# Export test directory for test scripts
export TEST_DIR

# Run tests
echo "Running tests..."

PROVIDER="openai"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done
shift $((OPTIND -1))

if [ $# -eq 0 ]; then
    # If no arguments provided, run all tests
    test_files=(scripts/*.sh)
else
    # If arguments provided, use them as test files
    test_files=("$1")  # Only take the first argument as the test file
fi

PROVIDER="openai"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done
shift $((OPTIND -1))

for test in "${test_files[@]}"; do
    if [ ! -f "$test" ]; then
        echo "❌ Test file not found: $test"
        failed_tests=1
        continue
    fi
    
    echo "Running $test..."
    if bash "$test" -p "$PROVIDER"; then
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