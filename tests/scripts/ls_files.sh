#!/bin/bash

# Test listing files in the test directory
output=$(../bin/cli.sh -t 0 "ls -1 $TEST_DIR")
echo "Raw output:"
echo "$output"

# Extract the plain text output between ```plaintext marks
actual_output=$(echo "$output" | sed -n '/^```plaintext$/,/^```$/p' | sed '1d;$d' | grep -v '^$' | tr -d '\r')
echo "Processed output:"
echo "$actual_output"

# Compare with expected output
if [ "$(echo "$actual_output" | grep -c "test[12]")" -eq 2 ]; then
    exit 0
else
    echo "Expected to find test1.txt and test2.py in output:"
    echo "$actual_output"
    exit 1
fi
