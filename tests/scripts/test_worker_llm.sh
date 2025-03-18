#!/bin/bash

# Test the worker_llm module functionality
# This test verifies that both synchronous and asynchronous worker LLM functions
# work correctly with different providers

PROVIDER="anthropic"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done
shift $((OPTIND -1))

# Ensure API keys are available to the test script
if [ -f ~/.openai ]; then
    export OPENAI_API_KEY=$(cat ~/.openai)
fi

if [ -f ~/.anthropic/api_key ]; then
    export ANTHROPIC_API_KEY=$(cat ~/.anthropic/api_key)
fi

# Copy the worker_llm_patch.py script to the test directory
cp /home/dror/vmpilot/tests/scripts/worker_llm_patch.py "$TEST_DIR/"
chmod +x "$TEST_DIR/worker_llm_patch.py"

# Run the patch script
echo "Patching worker_llm module to use environment variables directly..."
python3 "$TEST_DIR/worker_llm_patch.py"

# Create a test script to run the patched worker_llm module
TEST_SCRIPT="$TEST_DIR/test_worker_llm_script.py"

cat > "$TEST_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
Test script for worker_llm module.

This script tests both synchronous and asynchronous worker LLM functions
with a simple prompt and verifies the output.
"""

import asyncio
import sys
import os
import json
import importlib.util
import pathlib

# First, import and run our patch
current_dir = pathlib.Path(__file__).parent
patch_path = current_dir / "worker_llm_patch.py"
spec = importlib.util.spec_from_file_location("worker_llm_patch", patch_path)
patch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch_module)

# Now import the patched worker_llm module
from vmpilot.worker_llm import run_worker, run_worker_async
from vmpilot.config import Provider
import argparse

def test_sync_worker(provider_name):
    """Test the synchronous worker."""
    provider = getattr(Provider, provider_name.upper())
    prompt = "What is the capital of France? Respond with just the city name, nothing else."
    system_prompt = "You are a helpful assistant that provides concise, accurate answers."
    
    print(f"Testing synchronous worker with provider: {provider_name}")
    try:
        result = run_worker(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=provider,
            temperature=0,  # Use temperature 0 for deterministic results
        )
        print(f"Sync result: {result}")
        return result
    except Exception as e:
        print(f"Error in sync worker: {str(e)}")
        return None

async def test_async_worker(provider_name):
    """Test the asynchronous worker."""
    provider = getattr(Provider, provider_name.upper())
    prompt = "What is the capital of Germany? Respond with just the city name, nothing else."
    system_prompt = "You are a helpful assistant that provides concise, accurate answers."
    
    print(f"Testing asynchronous worker with provider: {provider_name}")
    try:
        result = await run_worker_async(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=provider,
            temperature=0,  # Use temperature 0 for deterministic results
        )
        print(f"Async result: {result}")
        return result
    except Exception as e:
        print(f"Error in async worker: {str(e)}")
        return None

async def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description='Test worker_llm module')
    parser.add_argument('--provider', '-p', default='openai', help='Provider to use (openai or anthropic)')
    args = parser.parse_args()
    
    results = {
        "sync": None,
        "async": None,
        "success": False
    }
    
    # Run synchronous test
    results["sync"] = test_sync_worker(args.provider)
    
    # Run asynchronous test
    results["async"] = await test_async_worker(args.provider)
    
    # Check if both tests were successful
    if results["sync"] and results["async"]:
        # Verify that the responses are appropriate
        sync_success = "paris" in results["sync"].lower()
        async_success = "berlin" in results["async"].lower()
        results["success"] = sync_success and async_success
        
        if not sync_success:
            print(f"Sync test failed: Expected 'Paris' in response, got: {results['sync']}")
        if not async_success:
            print(f"Async test failed: Expected 'Berlin' in response, got: {results['async']}")
    
    # Output results as JSON for the bash script to parse
    print(json.dumps(results))
    
    # Return appropriate exit code
    sys.exit(0 if results["success"] else 1)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Make the test script executable
chmod +x "$TEST_SCRIPT"

echo "Running worker_llm tests with provider: $PROVIDER"
python3 "$TEST_SCRIPT" --provider "$PROVIDER"

# Get the exit code from the Python script
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ Worker LLM tests passed successfully"
    exit 0
else
    echo "❌ Worker LLM tests failed"
    exit 1
fi
