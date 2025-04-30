"""
Unit tests for the database connection module.

Tests the database connection management functionality.
"""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vmpilot.db.connection import (
    close_db_connection,
    get_db_connection,
    get_db_path,
    initialize_db,
)


class TestDatabaseConnectionManagement(unittest.TestCase):
    """Test cases for database connection management functions."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for the database
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        # Patch the get_db_path function to return our test path
        self.path_patcher = patch("vmpilot.db.connection.get_db_path")
        self.mock_get_path = self.path_patcher.start()
        self.mock_get_path.return_value = self.db_path

        # Patch the logger
        self.logger_patcher = patch("vmpilot.db.connection.logger")
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        # Stop patchers
        self.path_patcher.stop()
        self.logger_patcher.stop()

        # Remove the temporary directory
        self.temp_dir.cleanup()

    @patch("vmpilot.db.connection._db_connection", None)
    def test_close_db_connection_when_no_connection(self):
        """Test closing the database connection when no connection exists."""
        # Call the function with no existing connection
        close_db_connection()

        # Verify that no error occurs and no logging happens
        self.mock_logger.info.assert_not_called()
        self.mock_logger.error.assert_not_called()

    @patch("vmpilot.db.connection._db_connection")
    def test_close_db_connection_success(self, mock_connection):
        """Test successfully closing an existing database connection."""
        # Set up mock connection
        mock_connection.close = MagicMock()

        # Call the function
        close_db_connection()

        # Verify that close was called and logged
        mock_connection.close.assert_called_once()
        self.mock_logger.info.assert_called_once_with("Closing database connection")
        self.mock_logger.error.assert_not_called()

        # Verify that the global connection was set to None
        from vmpilot.db.connection import _db_connection

        self.assertIsNone(_db_connection)

    @patch("vmpilot.db.connection._db_connection")
    def test_close_db_connection_with_error(self, mock_connection):
        """Test handling errors when closing the database connection."""
        # Set up mock connection to raise an exception
        mock_connection.close = MagicMock(side_effect=Exception("Connection error"))

        # Call the function
        close_db_connection()

        # Verify that the error was logged
        self.mock_logger.info.assert_called_once_with("Closing database connection")
        self.mock_logger.error.assert_called_once()
        self.assertIn(
            "Error closing database connection", self.mock_logger.error.call_args[0][0]
        )

    @patch("vmpilot.db.connection.config")
    def test_get_db_path_with_config(self, mock_config):
        """Test getting the database path from configuration."""
        # Stop the path patcher to test the real function
        self.path_patcher.stop()

        # Set up mock config - use a path that doesn't require root permissions
        mock_config.database_config.path = "/tmp/custom/path/to/db.sqlite"
        mock_config.is_database_enabled.return_value = True

        # Call the function
        result = get_db_path()

        # Verify the result
        self.assertEqual(result, Path("/tmp/custom/path/to/db.sqlite"))

        # Restart the path patcher for other tests
        self.mock_get_path = self.path_patcher.start()
        self.mock_get_path.return_value = self.db_path

    @patch("vmpilot.db.connection.config")
    @patch("vmpilot.db.connection.Path.exists")
    @patch("vmpilot.db.connection.Path.mkdir")
    def test_get_db_path_creates_directory(self, mock_mkdir, mock_exists, mock_config):
        """Test that get_db_path creates the parent directory if it doesn't exist."""
        # Stop the path patcher to test the real function
        self.path_patcher.stop()

        # Set up mocks - use a path that doesn't require root permissions
        mock_config.database_config.path = "/tmp/custom/path/to/db.sqlite"
        mock_config.is_database_enabled.return_value = True
        mock_exists.return_value = False

        # Call the function
        result = get_db_path()

        # Verify that mkdir was called with parents=True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify the result
        self.assertEqual(result, Path("/tmp/custom/path/to/db.sqlite"))

        # Restart the path patcher for other tests
        self.mock_get_path = self.path_patcher.start()
        self.mock_get_path.return_value = self.db_path

    @patch("vmpilot.db.connection.config")
    @patch("os.path.exists")
    @patch("vmpilot.db.connection.Path.mkdir")
    @patch("vmpilot.db.connection.Path.home")
    def test_get_db_path_permission_error(
        self, mock_home, mock_mkdir, mock_exists, mock_config
    ):
        """Test get_db_path handles permission errors correctly."""
        # Stop the path patcher to test the real function
        self.path_patcher.stop()

        # Set up mocks
        mock_config.is_database_enabled.return_value = True
        delattr(mock_config, "database_config")  # Ensure we use the default path
        mock_exists.return_value = False  # /app/data doesn't exist

        # Create a fake home directory
        fake_home = Path(self.temp_dir.name) / "home" / "testuser"
        mock_home.return_value = fake_home

        # Mock mkdir to raise PermissionError on first call
        mock_mkdir.side_effect = [PermissionError("Permission denied"), None]

        # Call the function under test
        path = get_db_path()

        # Verify that it falls back to home directory
        self.assertEqual(path, fake_home / ".vmpilot" / "vmpilot.db")

        # Restart the path patcher for other tests
        self.mock_get_path = self.path_patcher.start()
        self.mock_get_path.return_value = self.db_path

    @patch("vmpilot.db.connection.config")
    @patch("os.path.exists")
    @patch("vmpilot.db.connection.Path.mkdir")
    @patch("vmpilot.db.connection.Path.home")
    def test_get_db_path_file_not_found_error(
        self, mock_home, mock_mkdir, mock_exists, mock_config
    ):
        """Test get_db_path handles FileNotFoundError correctly."""
        # Stop the path patcher to test the real function
        self.path_patcher.stop()

        # Set up mocks
        mock_config.is_database_enabled.return_value = True
        delattr(mock_config, "database_config")  # Ensure we use the default path
        mock_exists.return_value = False  # /app/data doesn't exist

        # Create a fake home directory
        fake_home = Path(self.temp_dir.name) / "home" / "testuser"
        mock_home.return_value = fake_home

        # Mock mkdir to raise FileNotFoundError on first call
        mock_mkdir.side_effect = [FileNotFoundError("No such file or directory"), None]

        # Call the function under test
        path = get_db_path()

        # Verify that it falls back to home directory
        self.assertEqual(path, fake_home / ".vmpilot" / "vmpilot.db")

        # Restart the path patcher for other tests
        self.mock_get_path = self.path_patcher.start()
        self.mock_get_path.return_value = self.db_path

    @patch("vmpilot.db.connection.config")
    def test_get_db_path_with_user_directory(self, mock_config):
        """Test that get_db_path expands user directories."""
        # Stop the path patcher to test the real function
        self.path_patcher.stop()

        # Set up mock config with a path that includes ~
        mock_config.database_config.path = "~/path/to/db.sqlite"
        mock_config.is_database_enabled.return_value = True

        # Call the function
        result = get_db_path()

        # Verify the result is expanded
        self.assertEqual(result, Path(os.path.expanduser("~/path/to/db.sqlite")))

        # Restart the path patcher for other tests
        self.mock_get_path = self.path_patcher.start()
        self.mock_get_path.return_value = self.db_path


if __name__ == "__main__":
    unittest.main()
