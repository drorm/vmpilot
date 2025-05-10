#!/bin/bash
set -e

# Use absolute paths for reliability
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$ROOT_DIR/reports"

# Ensure reports directory exists
mkdir -p "$REPORTS_DIR"

echo "Running pyright type checking..."
# No need to specify config file as it will use pyproject.toml automatically

# Save a human-readable version for quick review
cd "$ROOT_DIR" && pyright ./src/ > "$REPORTS_DIR/pyright-report.txt" 2>&1 || true

echo "Type checking complete. Reports saved to $REPORTS_DIR/pyright-report.txt"

# Check if the report file exists
if [ ! -f "$REPORTS_DIR/pyright-report.txt" ]; then
    echo "Error: Report file was not created"
    exit 1
fi

# Exit with error if there were issues (for CI/CD pipelines)
if grep -q "error:" "$REPORTS_DIR/pyright-report.txt"; then
    echo "⚠️ Type checking found issues. See report for details."
    exit 1
else
    echo "✅ Type checking passed successfully!"
fi
