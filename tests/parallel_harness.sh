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
echo "Running tests in parallel..."

PROVIDER="anthropic"
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
    test_files=("$@")
fi

# Create a results directory
RESULTS_DIR="$TEST_DIR/results"
mkdir -p "$RESULTS_DIR"

# Array to store the PIDs of the background processes
declare -a pids=()
declare -a test_names=()

# Calculate total number of tests
total_tests=${#test_files[@]}
completed_tests=0

# Run all tests in parallel
for test in "${test_files[@]}"; do
    if [ ! -f "$test" ]; then
        echo "❌ Test file not found: $test"
        echo "$test: NOTFOUND" > "$RESULTS_DIR/$(basename "$test").result"
        ((completed_tests++))
        echo "Progress: $completed_tests/$total_tests tests completed"
        continue
    fi
    
    test_name=$(basename "$test")
    test_names+=("$test_name")
    echo "Starting $test..."
    
    # Run the test in the background and capture its pid
    (
        if bash "$test" -p "$PROVIDER" > "$RESULTS_DIR/$test_name.log" 2>&1; then
            echo "$test_name: PASS" > "$RESULTS_DIR/$test_name.result"
        else
            echo "$test_name: FAIL" > "$RESULTS_DIR/$test_name.result"
        fi
        
        # Update the completed tests counter using a lockfile to avoid race conditions
        (
            flock -x 200
            current=$(cat "$RESULTS_DIR/completed_count" 2>/dev/null || echo "0")
            echo $((current + 1)) > "$RESULTS_DIR/completed_count"
            completed=$(cat "$RESULTS_DIR/completed_count")
            echo "✅ $test_name completed (Progress: $completed/$total_tests tests completed)"
        ) 200>"$RESULTS_DIR/count.lock"
    ) &
    
    pids+=($!)
done

# Initialize the completed tests counter
echo "0" > "$RESULTS_DIR/completed_count"

echo "All tests launched. Waiting for completion..."
echo "Running tests: ${test_names[*]}"
echo "Total tests to run: $total_tests"

# Wait for all tests to complete
for pid in "${pids[@]}"; do
    wait $pid
done

# Process results
echo "All tests completed. Results:"
echo "-------------------"

success_count=0
failure_count=0
not_found_count=0

for result_file in "$RESULTS_DIR"/*.result; do
    # Skip the completed_count file if it exists in the results directory
    if [[ $(basename "$result_file") == "completed_count" ]]; then
        continue
    fi
    
    result=$(cat "$result_file")
    test_name=$(echo "$result" | cut -d':' -f1)
    status=$(echo "$result" | cut -d':' -f2 | tr -d ' ')
    
    case "$status" in
        "PASS")
            echo "✅ $test_name passed"
            ((success_count++))
            ;;
        "FAIL")
            echo "❌ $test_name failed"
            echo "--- Log output ---"
            cat "$RESULTS_DIR/$test_name.log"
            echo "-----------------"
            ((failure_count++))
            ;;
        "NOTFOUND")
            echo "❓ $test_name not found"
            ((not_found_count++))
            ;;
    esac
    echo "-------------------"
done

# Summary
echo "SUMMARY:"
echo "✅ Passed: $success_count"
echo "❌ Failed: $failure_count"
echo "❓ Not found: $not_found_count"
echo "Total: $((success_count + failure_count + not_found_count))"

# Cleanup
echo "Cleaning up test environment..."
rm -rf "$TEST_DIR"

# Exit with status
if [ "$failure_count" -gt 0 ] || [ "$not_found_count" -gt 0 ]; then
    exit 1
else
    echo "All tests passed! 🎉"
    exit 0
fi
