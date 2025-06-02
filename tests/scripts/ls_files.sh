#!/bin/bash

# Test listing files in the test directory
PROVIDER="openai"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done
shift $((OPTIND -1))

# Use the run_cli.sh wrapper script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output=$("$SCRIPT_DI"$SCRIPT_DIR/run_cli.sh"" -p "$PROVIDER" -t 0 "ls -1 $TEST_DIR | sort")
echo "Contents of TEST_DIR before executing cli.sh:" && ls -1 $TEST_DIR
echo "Raw output:"
echo "$output"

# Extract the plain text output - handle both formats
actual_output=$(echo "$output" | grep -o "\`test[12]\.[a-z]*\`\|\btest[12]\.[a-z]*\b" | tr -d '\`' | sort -u)
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
