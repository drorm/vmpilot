#!/bin/bash
# Fail on any error
set -e

# Get the directory where the script is located and move up one level to root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export VMPILOT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Setup pipeline directory - use environment variable if set, otherwise use default
PIPELINES_DIR="${VMPILOT_PIPELINES_DIR:-/app/pipelines}"

# Setup pipeline directory
cd "$PIPELINES_DIR"
rm -f vmpilot
ln -s "$VMPILOT_ROOT/src/vmpilot" vmpilot

cd pipelines
# Clean up any existing compute directory and files
rm -f "vmpilot.py"
# Link necessary files into compute directory
ln -s "$VMPILOT_ROOT/src/vmpilot/vmpilot.py"

cd ..

# Set logging level for better visibility
export PYTHONLOGLEVEL=INFO

# Start the application
"./dev.sh"
