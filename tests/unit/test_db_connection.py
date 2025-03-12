"""
Test the database connection functionality.
"""

import os
import unittest
from pathlib import Path

from vmpilot.config import DATA_DIR, DB_PATH
from vmpilot.db.connection import get_db_connection, get_db_path


class TestDatabaseConnection(unittest.TestCase):
    """Test cases for database connection functionality."""

    def test_get_db_path(self):
        """Test that get_db_path returns the correct path from config."""
        db_path = get_db_path()
        # Check that the path is a Path object
        self.assertIsInstance(db_path, Path)
        # Check that the path matches the expected path from config
        self.assertEqual(str(db_path), DB_PATH)

    def test_db_connection(self):
        """Test that the database connection works."""
        # Get a connection to the database
        conn = get_db_connection()
        # Check that the connection is valid
        self.assertIsNotNone(conn)
        # Verify we can execute a simple query
        cursor = conn.execute("SELECT sqlite_version();")
        version = cursor.fetchone()[0]
        self.assertIsNotNone(version)
        print(f"SQLite version: {version}")

    def test_data_directory_created(self):
        """Test that the data directory is created."""
        # Verify the data directory exists
        self.assertTrue(os.path.exists(DATA_DIR))


if __name__ == "__main__":
    unittest.main(verbosity=2)
