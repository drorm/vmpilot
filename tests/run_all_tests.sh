#!/bin/bash
# Comprehensive test script for VMPilot
# This script runs all test components:
# 1. Unit tests
# 2. Coverage analysis
# 3. End-to-end tests
# 4. Type checking with pyright
# 5. Dependency analysis with deptry

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
REPORTS_DIR="$PROJECT_ROOT/reports"
TEST_DIR="$PROJECT_ROOT/tests"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT_FILE="$REPORTS_DIR/test_report_$TIMESTAMP.txt"

# Ensure reports directory exists
mkdir -p "$REPORTS_DIR"

# Initialize the report file
echo "VMPilot Test Report - $TIMESTAMP" > "$REPORT_FILE"
echo "=======================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Function to log messages to both console and report file
log() {
    echo "$1"
    echo "$1" >> "$REPORT_FILE"
}

# Function to run a test component and log its result
run_test_component() {
    local name="$1"
    local command="$2"
    local start_time=$(date +%s)

    log "Running $name..."
    log "----------------------------------------"

    # Create a temporary file for the output
    local temp_output=$(mktemp)

    # Run the command and capture its exit status
    if eval "$command" > "$temp_output" 2>&1; then
        local status="PASSED"
    else
        local status="FAILED"
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Log the output
    cat "$temp_output" | tee -a "$REPORT_FILE"
    rm "$temp_output"

    log ""
    log "$name: $status (Duration: ${duration}s)"
    log ""

    # Return the exit status (0 for success, non-zero for failure)
    return $([ "$status" = "PASSED" ] && echo 0 || echo 1)
}

# Track overall test status
overall_status=0

# 1. Run coverage analysis
log "Step 1: Running coverage analysis"
if ! run_test_component "Coverage Analysis" "cd $PROJECT_ROOT && bash $TEST_DIR/coverage.sh"; then
    overall_status=1
fi

# 2. Run pyright type checking
log "Step 2: Running pyright type checking"
if ! run_test_component "Pyright Type Checking" "cd $PROJECT_ROOT && bash $TEST_DIR/pyright.sh"; then
    overall_status=1
fi

# 3. Run deptry dependency analysis
log "Step 3: Running deptry dependency analysis"
if ! run_test_component "Deptry Dependency Analysis" "cd $PROJECT_ROOT && deptry ."; then
    overall_status=1
fi

# Generate summary
log "Summary"
log "======================================="

if [ $overall_status -eq 0 ]; then
    log "✅ All tests passed successfully!"
else
    log "❌ Some tests failed. Check the report for details."
fi

# Make the report file more accessible
log "Test report saved to: $REPORT_FILE"
cp "$REPORT_FILE" "$REPORTS_DIR/latest_test_report.txt"
log "A copy of the report is also available at: $REPORTS_DIR/latest_test_report.txt"

exit $overall_status
