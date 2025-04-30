#!/bin/bash
# Wrapper script for running the CLI with or without coverage
# Usage: ./run_cli.sh [arguments for cli.sh]

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the root directory of the project
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# CLI script path with absolute path
CLI_SCRIPT="$PROJECT_ROOT/bin/cli.sh"

# Check if coverage is enabled via environment variable
if [ -n "$VMPILOT_COVERAGE" ]; then
    # Add coverage flag to arguments
    "$CLI_SCRIPT" --coverage "$@"
else
    # Run normally without coverage
    "$CLI_SCRIPT" "$@"
fi
