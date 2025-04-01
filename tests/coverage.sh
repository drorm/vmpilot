#!/bin/bash
# Script to run code coverage analysis for VMPilot
# This script performs the following:
# 1. Erases existing coverage data
# 2. Runs unit tests with coverage
# 3. Runs e2e tests with coverage
# 4. Generates and displays coverage report

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
REPORTS_DIR="$PROJECT_ROOT/reports"
cd "$PROJECT_ROOT"

echo "Starting code coverage analysis for VMPilot..."
echo "Project root: $PROJECT_ROOT"

# Process command line arguments
FAIL_UNDER=70
while getopts "f:" opt; do
  case $opt in
    f) FAIL_UNDER="$OPTARG" ;;
  esac
done

# Step 1: Erase existing coverage data
echo "Erasing existing coverage data..."
python -m coverage erase

# Step 2: Run unit tests with coverage
echo "Running unit tests with coverage..."
# Use --no-cov-on-fail to ensure coverage data is saved even if tests fail
python -m pytest -q --cov=src/vmpilot --cov-report= --no-cov-on-fail tests/unit || true

# Save unit test coverage
mv .coverage .coverage.unit

# Step 3: Run e2e tests with coverage
echo "Running end-to-end tests with coverage..."
# Export environment variable for test scripts to detect coverage mode
export VMPILOT_COVERAGE=1
export COVERAGE_PROCESS_START=$PROJECT_ROOT/.coveragerc

# Run e2e tests 
"$PROJECT_ROOT/tests/e2e_tests.sh" || true

# Step 4: Generate and display coverage report
echo "Combining coverage data..."
python -m coverage combine .coverage.*

echo "Generating coverage report..."
python -m coverage report --fail-under=$FAIL_UNDER > $REPORTS_DIR/coverage.txt || true

echo "Coverage reports saved to $REPORTS_DIR"
echo "To combine with pipeline coverage, run bin/combine_coverage.sh after running pipeline tests"
