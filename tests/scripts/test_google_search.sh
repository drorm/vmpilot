#!/bin/bash

# End-to-end test for Google Search functionality
# This test verifies that the Google Search tool is properly integrated and can return search results.

# Get script directory for accessing helper scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Setup - check if required environment variables are available
if [ -z "$GOOGLE_API_KEY" ] || [ -z "$GOOGLE_CSE_ID" ]; then
    echo "Warning: GOOGLE_API_KEY and/or GOOGLE_CSE_ID environment variables are not set."
    echo "This test will verify that the tool correctly handles missing configuration."
    EXPECT_CONFIG_ERROR=true
else
    EXPECT_CONFIG_ERROR=false
fi

echo "=== Testing Google Search Functionality ==="

# Create a temporary file to store results
RESULTS_FILE=$(mktemp)

# Test 1: Basic search functionality
echo "Test 1: Basic search query..."
SEARCH_QUERY="foo"
"$SCRIPT_DIR/run_cli.sh" -t 0 "search for $SEARCH_QUERY using google search" > "$RESULTS_FILE" 2>&1

# Check the results
if $EXPECT_CONFIG_ERROR; then
    # If we expect a configuration error, check for the error message
    if grep -q "Google Search API is not properly configured" "$RESULTS_FILE"; then
        echo "✅ Test 1: Tool correctly reported configuration error."
    else
        echo "❌ Test 1: Expected configuration error message not found."
        echo "Output:"
        cat "$RESULTS_FILE"
        rm "$RESULTS_FILE"
        exit 1
    fi
else
    # If we have proper configuration, check for search results
    if grep -q "https://" "$RESULTS_FILE" && grep -q "Fighters" "$RESULTS_FILE" -i; then
        echo "✅ Test 1: Search returned results containing the expected term."
    else
        echo "❌ Test 1: Search did not return expected results."
        echo "Output:"
        cat "$RESULTS_FILE"
        rm "$RESULTS_FILE"
        exit 1
    fi
fi

echo "=== All Google Search tests completed successfully ==="
exit 0
