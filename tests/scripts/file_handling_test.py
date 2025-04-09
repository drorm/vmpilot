#!/usr/bin/env python3
"""
Test script specifically targeting the file handling functionality in cli.py
"""
import io
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

import coverage

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestCLIFileHandling(unittest.TestCase):
    """Test case for file handling in cli.py"""

    def setUp(self):
        """Set up the test environment"""
        # Create a temporary file for testing file input
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w+")
        self.temp_file.write("echo 'Test from file'\n")
        self.temp_file.write("# This is a comment\n")
        self.temp_file.write("\n")  # Empty line
        self.temp_file.write("echo 'Another command'\n")
        self.temp_file.close()

        # Create a non-readable file
        self.non_readable_file = tempfile.NamedTemporaryFile(delete=False, mode="w+")
        self.non_readable_file.write("echo 'Test from non-readable file'\n")
        self.non_readable_file.close()
        os.chmod(self.non_readable_file.name, 0o000)  # Make file non-readable

        # Create a binary file
        self.binary_file = tempfile.NamedTemporaryFile(delete=False, mode="wb")
        self.binary_file.write(b"\x00\x01\x02\x03")
        self.binary_file.close()

    def tearDown(self):
        """Clean up after tests"""
        # Remove the temporary files
        os.unlink(self.temp_file.name)
        os.chmod(
            self.non_readable_file.name, 0o666
        )  # Make file readable again for deletion
        os.unlink(self.non_readable_file.name)
        os.unlink(self.binary_file.name)

    @patch("asyncio.run")
    @patch("builtins.print")
    def test_file_processing_normal(self, mock_print, mock_asyncio_run):
        """Test processing a normal file with commands"""
        from src.vmpilot.cli import main

        # Mock sys.argv
        with patch("sys.argv", ["cli.py", "-f", self.temp_file.name]):
            # Execute the main function
            main()

            # Assert that asyncio.run was called twice (for the two commands)
            self.assertEqual(mock_asyncio_run.call_count, 2)

    @patch("sys.exit")
    @patch("builtins.print")
    def test_file_not_found(self, mock_print, mock_exit):
        """Test handling a non-existent file"""
        from src.vmpilot.cli import main

        # Mock sys.argv
        with patch("sys.argv", ["cli.py", "-f", "/nonexistent/file.txt"]):
            # Execute the main function
            main()

            # Assert that sys.exit was called with error code
            mock_exit.assert_called_once_with(1)

    @patch("sys.exit")
    @patch("builtins.print")
    def test_file_permission_denied(self, mock_print, mock_exit):
        """Test handling a file with permission issues"""
        from src.vmpilot.cli import main

        # Mock sys.argv
        with patch("sys.argv", ["cli.py", "-f", self.non_readable_file.name]):
            # Execute the main function
            main()

            # Assert that sys.exit was called with error code
            mock_exit.assert_called_once_with(1)

    @patch("sys.exit")
    @patch("builtins.print")
    def test_file_unicode_error(self, mock_print, mock_exit):
        """Test handling a binary file (should cause UnicodeDecodeError)"""
        from src.vmpilot.cli import main

        # Mock sys.argv
        with patch("sys.argv", ["cli.py", "-f", self.binary_file.name]):
            # Execute the main function
            main()

            # Assert that sys.exit was called with error code
            mock_exit.assert_called_once_with(1)

    @patch("builtins.print")
    def test_no_command_or_file(self, mock_print):
        """Test handling when neither command nor file is provided"""
        from src.vmpilot.cli import main

        # Mock sys.argv
        with patch("sys.argv", ["cli.py"]):
            # Execute the main function with proper error handling
            with self.assertRaises(SystemExit):
                main()


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
