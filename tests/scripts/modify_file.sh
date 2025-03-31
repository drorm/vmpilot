#!/bin/bash

# Test modifying a file
test_file="$TEST_DIR/test2.py"

# Store initial content
initial_content=$(cat "$test_file")

# Run modification command using the wrapper script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output=$("$SCRIPT_DI"$SCRIPT_DIR/run_cli.sh"" -t 0 "Change 'This is a sample Python file' to 'This is a **very simple** Python file' in $test_file")

# Verify the change
if grep -q "This is a \*\*very simple\*\* Python file" "$test_file"; then
    # Verify rest of file is unchanged
    new_content=$(cat "$test_file")
    if [ "$(echo "$new_content" | wc -l)" = "$(echo "$initial_content" | wc -l)" ]; then
        exit 0
    else
        echo "File structure changed unexpectedly"
        echo "Before:"
        echo "$initial_content"
        echo "After:"
        echo "$new_content"
        exit 1
    fi
else
    echo "Expected modification not found in file"
    cat "$test_file"
    exit 1
fi
