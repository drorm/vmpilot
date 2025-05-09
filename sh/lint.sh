#!/bin/bash

PATH="$HOME/.local/bin:$PATH"
MYPY_CACHE_DIR="/tmp/mypy_cache"
# Get the git root directory instead of hardcoding the path
GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT"

set -e
echo "Running linting checks..."

# Run black check
echo "Running black check..."
python3 -m black --check .
if [ $? -ne 0 ]; then
    echo 'Black found files to reformat. Formatting them now...'
    python3 -m black .
    echo 'Please review and add the changes, then commit again.'
    exit 1
fi

# Run isort check
echo "Running isort check..."
python3 -m isort --check-only .
if [ $? -ne 0 ]; then
    echo 'Isort found files to reformat. Formatting them now...'
    python3 -m isort .
    echo 'Please review and add the changes, then commit again.'
    exit 1
fi

echo "✅ All linting checks passed!"
