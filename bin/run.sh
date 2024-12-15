#!/bin/bash
# Fail on any error
set -e

# Get the directory where the script is located and move up one level to root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Setup pipeline directory
PIPELINES_DIR=~/pipelines

# Setup pipeline directory
cd "$PIPELINES_DIR"
rm -f vmpilot
ln -s "$ROOT_DIR/src/vmpilot" vmpilot

cd pipelines
# Clean up any existing compute directory and files
rm -f "vmpilot.py"
# Link necessary files into compute directory
ln -s "$ROOT_DIR/src/vmpilot/vmpilot.py"

cd ..

# Start the application
"./dev.sh"
