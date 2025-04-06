#!/bin/bash
# This script tests various CLI functionality to improve coverage

# Set up
cd "$(dirname "$0")/../.."
CLI="bin/cli.sh --coverage"

# Test basic command
echo "Testing basic command execution..."
$CLI -v 'echo "Basic command test"'

# Test with debug mode
echo "Testing debug mode..."
$CLI -d 'echo "Debug mode test"'

# Test with file input
echo "Creating test file..."
echo 'echo "Command from file"' > /tmp/cli_test_commands.txt
echo "Testing file input..."
$CLI -f /tmp/cli_test_commands.txt

# Test with temperature setting
echo "Testing temperature setting..."
$CLI -t 0.5 'echo "Temperature test"'

# Test with provider setting
echo "Testing provider setting..."
$CLI -p openai 'echo "Provider test"'

# Test with Git options
echo "Testing Git options..."
$CLI --git 'echo "Git enabled test"'
$CLI --no-git 'echo "Git disabled test"'

# Test error handling (invalid file)
echo "Testing error handling (invalid file)..."
$CLI -f /nonexistent/file 2>/dev/null || echo "Error handled correctly"

# Clean up
rm -f /tmp/cli_test_commands.txt

# Combine coverage data
echo "Combining coverage data..."
coverage combine

# Show coverage report
echo "Coverage report:"
coverage report