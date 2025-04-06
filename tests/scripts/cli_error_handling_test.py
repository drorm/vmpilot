#!/usr/bin/env python3
"""
Test script specifically targeting error handling in cli.py
"""
import asyncio
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import coverage

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestCLIErrorHandling(unittest.TestCase):
    """Test case for error handling in cli.py"""

    @patch("asyncio.run")
    @patch("builtins.print")
    def test_keyboard_interrupt_command(self, mock_print, mock_asyncio_run):
        """Test handling a KeyboardInterrupt during command execution"""
        from src.vmpilot.cli import main

        # Make asyncio.run raise KeyboardInterrupt
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        # Mock sys.argv
        with patch("sys.argv", ["cli.py", 'echo "Test"']):
            # Mock sys.exit to prevent actual exit
            with patch("sys.exit") as mock_exit:
                # Execute the main function
                main()

                # Assert that sys.exit was called with SIGINT code
                mock_exit.assert_called_once_with(130)

    @patch("asyncio.run")
    @patch("builtins.print")
    def test_general_exception_command(self, mock_print, mock_asyncio_run):
        """Test handling a general exception during command execution"""
        from src.vmpilot.cli import main

        # Make asyncio.run raise Exception
        mock_asyncio_run.side_effect = Exception("Test exception")

        # Mock sys.argv
        with patch("sys.argv", ["cli.py", 'echo "Test"']):
            # Mock sys.exit to prevent actual exit
            with patch("sys.exit") as mock_exit:
                # Execute the main function
                main()

                # Assert that sys.exit was called with error code
                mock_exit.assert_called_once_with(1)

    @patch("asyncio.run")
    @patch("builtins.print")
    def test_keyboard_interrupt_file(self, mock_print, mock_asyncio_run):
        """Test handling a KeyboardInterrupt during file processing"""
        from src.vmpilot.cli import main

        # Create a temporary file for testing
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w+")
        temp_file.write("echo 'Test'\n")
        temp_file.close()

        # Make asyncio.run raise KeyboardInterrupt
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        try:
            # Mock sys.argv
            with patch("sys.argv", ["cli.py", "-f", temp_file.name]):
                # Mock sys.exit to prevent actual exit
                with patch("sys.exit") as mock_exit:
                    # Execute the main function
                    main()

                    # Assert that sys.exit was called with SIGINT code
                    mock_exit.assert_called_once_with(130)
        finally:
            # Clean up
            os.unlink(temp_file.name)

    @patch("asyncio.run")
    @patch("builtins.print")
    def test_general_exception_file(self, mock_print, mock_asyncio_run):
        """Test handling a general exception during file processing"""
        from src.vmpilot.cli import main

        # Create a temporary file for testing
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w+")
        temp_file.write("echo 'Test'\n")
        temp_file.close()

        # Make asyncio.run raise Exception
        mock_asyncio_run.side_effect = Exception("Test exception")

        try:
            # Mock sys.argv
            with patch("sys.argv", ["cli.py", "-f", temp_file.name]):
                # Mock sys.exit to prevent actual exit
                with patch("sys.exit") as mock_exit:
                    # Execute the main function
                    main()

                    # Assert that sys.exit was called with error code
                    mock_exit.assert_called_once_with(1)
        finally:
            # Clean up
            os.unlink(temp_file.name)

    @patch("sys.argv", ["cli.py", "--coverage", 'echo "Test"'])
    @patch("coverage.Coverage")
    @patch("asyncio.run")
    def test_coverage_flag(self, mock_asyncio_run, mock_coverage, _):
        """Test handling the coverage flag"""
        from src.vmpilot.cli import COVERAGE_AVAILABLE, main

        # Create a mock coverage object
        mock_cov = MagicMock()
        mock_coverage.return_value = mock_cov

        # Execute the main function
        main()

        # If coverage is available, verify it was used
        if COVERAGE_AVAILABLE:
            mock_cov.start.assert_called_once()
            mock_cov.stop.assert_called_once()
            mock_cov.save.assert_called_once()


class TestProcessCommand(unittest.TestCase):
    """Test case for the process_command function in cli.py"""

    @patch("vmpilot.vmpilot.Pipeline")
    async def test_process_command_success(self, mock_pipeline_class):
        """Test successful command processing"""
        from src.vmpilot.cli import process_command

        # Create a mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create a mock result generator
        mock_result = [
            "Test message 1",
            {"type": "text", "text": "Test message 2"},
            {
                "type": "tool_use",
                "name": "edit_file",
                "input": {"content": "Test edit"},
            },
            {"type": "tool_output", "output": "Test output", "error": None},
            {"type": "tool_output", "output": "", "error": "Test error"},
        ]
        mock_pipeline.pipe.return_value = mock_result

        # Execute the process_command function
        with patch("builtins.print") as mock_print:
            await process_command("echo 'Test'", 0.7, "anthropic", False)

            # Assert that print was called for each message
            self.assertEqual(mock_print.call_count, 5)

    @patch("vmpilot.vmpilot.Pipeline")
    async def test_process_command_exception(self, mock_pipeline_class):
        """Test command processing with exception"""
        from src.vmpilot.cli import process_command

        # Create a mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline

        # Make pipeline.pipe raise Exception
        mock_pipeline.pipe.side_effect = Exception("Test exception")

        # Execute the process_command function
        with patch("builtins.print") as mock_print:
            with self.assertRaises(Exception):
                await process_command("echo 'Test'", 0.7, "anthropic", False)


if __name__ == "__main__":
    # Start coverage
    cov = coverage.Coverage()
    cov.start()

    try:
        # Run the tests
        unittest.main(argv=["first-arg-is-ignored"], exit=False)
    finally:
        # Stop coverage
        cov.stop()
        cov.save()

        # Print coverage report
        print("\nCoverage report:")
        cov.report()
