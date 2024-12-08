#!/bin/bash

# Test creating and editing a file
test_file="/tmp/hello.py"
# Remove file if it exists to ensure the test runs correctly
if [ -f "$test_file" ]; then
    rm "$test_file"
fi


# Step 1: Create the file with initial content using cli.sh
output_create=$(/home/dror/vmpilot/bin/cli.sh -t 0 "create $test_file, hello world example")

echo "Create command output:\n$output_create"\n# Verify the creation
if echo "$output_create" | grep -q "File created"; then
    echo "File created successfully with hello world example."
else
    echo "Failed to create file with hello world example."
    exit 1
fi

# Step 2: Change the content to say goodbye
output_modify=$(/home/dror/vmpilot/bin/cli.sh -t 0 "change 'Hello' to 'Goodbye' in $test_file")

echo "Modify command output:\n$output_modify"\n# Verify the modification
if grep -q "print(\"Goodbye, World!\")" "$test_file"; then
    echo "File modified successfully to say goodbye."
    exit 0
else
    echo "Failed to modify file to say goodbye."
    cat "$test_file"
    exit 1
fi
