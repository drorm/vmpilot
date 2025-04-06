#!/bin/bash
# Run all CLI test scripts and combine coverage

# Set up
cd "$(dirname "$0")/../.."
rm -f .coverage*

# Run all test scripts
echo "Running direct_cli_test.py..."
tests/scripts/direct_cli_test.py

echo "Running file_handling_test.py..."
tests/scripts/file_handling_test.py

echo "Running cli_error_handling_test.py..."
tests/scripts/cli_error_handling_test.py

echo "Running comprehensive_cli_test.py..."
tests/scripts/comprehensive_cli_test.py

echo "Running cli_coverage_test.sh..."
tests/scripts/cli_coverage_test.sh

# Combine coverage data
echo "Combining coverage data..."
coverage combine

# Show coverage report
echo "Coverage report:"
coverage report