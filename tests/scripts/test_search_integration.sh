#!/bin/bash
# Integration test for the code search functionality

# Exit on error
set -e

echo "Running Code Search Integration Test"
echo "==================================="

# Test the standalone CLI tool
echo "Testing standalone CLI tool..."
python ~/vmpilot/src/codesearch/search.py --query "How does the shell tool work?" --project-root ~/vmpilot/src/vmpilot/tools --output-format markdown

# Test the VMPilot integration
# This would typically be done through the VMPilot CLI or API
# For this test, we're just verifying that the tool is properly registered

echo "Checking SearchTool registration in VMPilot..."
if grep -q "SearchTool" ~/vmpilot/src/vmpilot/tools/setup_tools.py; then
    echo "✅ SearchTool is properly registered in setup_tools.py"
else
    echo "❌ SearchTool is not properly registered in setup_tools.py"
    exit 1
fi

if grep -q "SearchTool" ~/vmpilot/src/vmpilot/tools/__init__.py; then
    echo "✅ SearchTool is properly exported in __init__.py"
else
    echo "❌ SearchTool is not properly exported in __init__.py"
    exit 1
fi

echo "Integration test completed successfully!"