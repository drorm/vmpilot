#!/bin/bash
# Script to properly combine coverage data from multiple sources

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT"

echo "Combining coverage data from multiple sources..."

# Step 1: Make sure we have the coverage data from both sources
if [ ! -f "$PROJECT_ROOT/.coverage" ]; then
    echo "Error: No base coverage file found at $PROJECT_ROOT/.coverage"
    exit 1
fi

if [ ! -f "$HOME/pipelines/.coverage" ]; then
    echo "Error: No pipeline coverage file found at $HOME/pipelines/.coverage"
    exit 1
fi

# Step 2: Copy the pipeline coverage with a unique name
echo "Copying pipeline coverage data..."
cp "$HOME/pipelines/.coverage" "$PROJECT_ROOT/.coverage.pipeline"

# Step 3: Combine the coverage data files
echo "Combining coverage data files..."
python -m coverage combine --append

# Step 4: Generate and display coverage report
echo "Generating combined coverage report..."
python -m coverage report

echo "Combined coverage report generated successfully."
echo "You can run 'coverage html' to generate an HTML report."
