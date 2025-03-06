#!/bin/bash

# Test conversation handling and context persistence
# This test simulates a multi-step conversation where context needs to be maintained

PROVIDER="openai"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done
shift $((OPTIND -1))

# Create temporary conversation file to maintain context
CONV_FILE=$(mktemp)
echo "Created conversation file: $CONV_FILE"

# Step 1: Initial query about /home directory and disk space
echo "Step 1: Asking about /home directory and disk space..."
output1=$(/home/dror/vmpilot/bin/cli.sh -p "$PROVIDER" -c "$CONV_FILE" "show me /home and then the total disk space for the user in there")

# Check if the output contains directory listing and disk usage
if echo "$output1" | grep -q "ls -la /home" && echo "$output1" | grep -q "du -sh /home"; then
    echo "✅ Step 1: First command executed successfully"
else
    echo "❌ Step 1: Failed to execute directory listing and disk usage commands"
    echo "Output: $output1"
    rm "$CONV_FILE"
    exit 1
fi

# Step 2: Follow-up query that requires context from the previous query
echo "Step 2: Asking follow-up question about files in user directory..."
output2=$(/home/dror/vmpilot/bin/cli.sh -p "$PROVIDER" -c "$CONV_FILE" "Show me 10 files in that user's dir")

# Check if the output contains a listing of files from the user directory
if echo "$output2" | grep -q "/home/dror" && (echo "$output2" | grep -q "ls" || echo "$output2" | grep -q "find"); then
    echo "✅ Step 2: Follow-up command executed successfully with context preserved"
else
    echo "❌ Step 2: Failed to maintain context or execute follow-up command"
    echo "Output: $output2"
    rm "$CONV_FILE"
    exit 1
fi

# Clean up
rm "$CONV_FILE"
echo "All conversation handling tests passed! 🎉"
exit 0