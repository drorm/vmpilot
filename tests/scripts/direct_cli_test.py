#!/usr/bin/env python3
"""
Direct test script for cli.py to improve coverage
"""
import os
import sys

import coverage

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Start coverage
cov = coverage.Coverage()
cov.start()

try:
    # Import the CLI module
    from src.vmpilot.cli import main, process_command

    # Create a test function to execute different code paths
    async def test_code_paths():
        # Test basic command processing
        await process_command("echo 'Basic test'", 0.7, "anthropic", False)

        # Test with debug flag
        await process_command("echo 'Debug test'", 0.7, "anthropic", True)

        # Test with different provider
        await process_command("echo 'Provider test'", 0.7, "openai", False)

        # Test with different temperature
        await process_command("echo 'Temperature test'", 0.5, "anthropic", False)

    # Mock sys.argv to test main() function with different arguments
    def test_main_function():
        # Save original argv
        original_argv = sys.argv.copy()

        try:
            # Test with basic command
            sys.argv = ["cli.py", "echo 'Main test'"]
            main()

            # Test with file input
            test_file = "/tmp/cli_test_file.txt"
            with open(test_file, "w") as f:
                f.write("echo 'File test'\n")

            sys.argv = ["cli.py", "-f", test_file]
            main()

            # Test with temperature
            sys.argv = ["cli.py", "-t", "0.5", "echo 'Temperature test'"]
            main()

            # Test with provider
            sys.argv = ["cli.py", "-p", "openai", "echo 'Provider test'"]
            main()

            # Test with debug flag
            sys.argv = ["cli.py", "-d", "echo 'Debug test'"]
            main()

            # Test with verbose flag
            sys.argv = ["cli.py", "-v", "echo 'Verbose test'"]
            main()

            # Test with git flag
            sys.argv = ["cli.py", "--git", "echo 'Git test'"]
            main()

            # Test with no-git flag
            sys.argv = ["cli.py", "--no-git", "echo 'No Git test'"]
            main()

            # Test with chat flag
            sys.argv = ["cli.py", "-c", "echo 'Chat test'"]
            main()

            # Test with coverage flag
            sys.argv = ["cli.py", "--coverage", "echo 'Coverage test'"]
            main()

            # Clean up
            os.remove(test_file)
        finally:
            # Restore original argv
            sys.argv = original_argv

    # Run tests
    import asyncio

    asyncio.run(test_code_paths())
    # test_main_function()  # Uncomment to test main function directly

finally:
    # Stop coverage
    cov.stop()
    cov.save()

    # Print coverage report
    print("\nCoverage report:")
    cov.report()
