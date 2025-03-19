#!/usr/bin/env python3
"""
Test script for worker_llm module.

This script demonstrates how to use the worker_llm module to run LLM tasks
both synchronously and asynchronously.
"""

import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from vmpilot.config import Provider
from vmpilot.worker_llm import run_worker, run_worker_async


def test_sync_worker():
    """Test the synchronous worker."""
    prompt = "Explain the concept of recursion in programming in one paragraph."
    system_prompt = "You are a helpful assistant that explains programming concepts clearly and concisely."

    result = run_worker(
        prompt=prompt,
        system_prompt=system_prompt,
        model="gpt-3.5-turbo",
        provider=Provider.OPENAI,
        temperature=0.2,
    )

    print("\n=== Synchronous Worker Result ===")
    print(result)
    print("================================\n")


async def test_async_worker():
    """Test the asynchronous worker."""
    prompt = "Explain the concept of concurrency in programming in one paragraph."
    system_prompt = "You are a helpful assistant that explains programming concepts clearly and concisely."

    result = await run_worker_async(
        prompt=prompt,
        system_prompt=system_prompt,
        model="gpt-3.5-turbo",
        provider=Provider.OPENAI,
        temperature=0.2,
    )

    print("\n=== Asynchronous Worker Result ===")
    print(result)
    print("==================================\n")


async def main():
    """Run all tests."""
    # Run synchronous test
    test_sync_worker()

    # Run asynchronous test
    await test_async_worker()


if __name__ == "__main__":
    asyncio.run(main())
