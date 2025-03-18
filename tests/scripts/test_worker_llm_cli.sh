#!/bin/bash

# Test the worker_llm module functionality through the CLI
# This test creates a Python script that uses the worker_llm module and then
# uses the CLI to execute it

PROVIDER="openai"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done
shift $((OPTIND -1))

# Copy the worker_llm_patch.py script to the test directory
cp /home/dror/vmpilot/tests/scripts/worker_llm_patch.py "$TEST_DIR/"
chmod +x "$TEST_DIR/worker_llm_patch.py"

# Run the patch script
echo "Patching worker_llm module to use environment variables directly..."
python3 "$TEST_DIR/worker_llm_patch.py"

# Create a test Python script that uses worker_llm with our patch
TEST_SCRIPT="$TEST_DIR/use_worker_llm.py"

cat > "$TEST_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
Example script demonstrating how to use the worker_llm module.
"""

import asyncio
import sys
import os
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

async def main():
    # Test synchronous worker
    provider_name = sys.argv[1] if len(sys.argv) > 1 else "OPENAI"
    provider = getattr(Provider, provider_name.upper())
    
    # Run sync worker
    sync_result = run_worker(
        prompt="What is 2 + 2? Answer with just the number.",
        system_prompt="You are a helpful, precise assistant.",
        provider=provider,
        temperature=0,
    )
    print(f"Sync result: {sync_result}")
    
    # Run async worker
    async_result = await run_worker_async(
        prompt="What is 3 × 3? Answer with just the number.",
        system_prompt="You are a helpful, precise assistant.",
        provider=provider,
        temperature=0,
    )
    print(f"Async result: {async_result}")

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Make the script executable
chmod +x "$TEST_SCRIPT"

# Create a test command for the CLI
CLI_COMMAND="python3 $TEST_SCRIPT $PROVIDER"

echo "Running worker_llm CLI test with provider: $PROVIDER"
output=$(/home/dror/vmpilot/bin/cli.sh -p "$PROVIDER" -t 0 "Run this script and explain what it does: $TEST_SCRIPT")

echo "Raw output:"
echo "$output"

# Check if the output contains the expected results
if echo "$output" | grep -q "Sync result" && echo "$output" | grep -q "Async result"; then
    # Further check if the results contain the correct answers
    if echo "$output" | grep -q "2 + 2" && echo "$output" | grep -q "3 × 3"; then
        echo "✅ Worker LLM CLI test passed"
        exit 0
    else
        echo "❌ Worker LLM CLI test failed: Missing expected calculations in output"
        exit 1
    fi
else
    echo "❌ Worker LLM CLI test failed: Missing expected worker results in output"
    exit 1
fi
