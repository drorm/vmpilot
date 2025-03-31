#!/bin/bash
set -e

ROOT_DIR=".."
# Use the existing reports directory
REPORTS_DIR="$ROOT_DIR/reports"

echo "Running mypy type checking..."
# No need to specify config file as it will use pyproject.toml automatically

# Also save a human-readable version for quick review
mypy --cache-dir=/tmp/mypy_cache --incremental $ROOT_DIR/src/ > $REPORTS_DIR/mypy-report.txt 2>&1 || true

echo "Type checking complete. Reports saved to $REPORTS_DIR/mypy-report.json and $REPORTS_DIR/mypy-report.txt"

# Exit with error if there were issues (for CI/CD pipelines)
if grep -q "^Found " $REPORTS_DIR/mypy-report.txt; then
    echo "⚠️ Type checking found issues. See report for details."
    exit 1
else
    echo "✅ Type checking passed successfully!"
fi
