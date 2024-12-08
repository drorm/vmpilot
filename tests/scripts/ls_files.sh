#!/bin/bash

# Test listing files in the test directory
PROVIDER="openai"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done
shift $((OPTIND -1))

output=$(/home/dror/vmpilot/bin/cli.sh -p "$PROVIDER" -t 0 "ls -1 $TEST_DIR")
echo "Contents of TEST_DIR before executing cli.sh:" && ls -1 $TEST_DIR
echo "Raw output:"
echo "$output"

# Extract the plain text output - handle both formats
actual_output=$(echo "$output" | grep -A 10 "Executing command:" | grep -v "Executing command:" | grep -o "test[12]\.[a-z]*" | sort -u)
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
