"""
Unit tests for database configuration.
"""

import os
import tempfile
import unittest
from configparser import ConfigParser
from pathlib import Path
from unittest.mock import patch

from vmpilot.config import ModelConfig


class TestDatabaseConfig(unittest.TestCase):
    """Test cases for database configuration."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for the config file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.ini"

    def tearDown(self):
        """Clean up test environment."""
        # Remove the temporary directory
        self.temp_dir.cleanup()

    def create_config(self, db_enabled=True, db_path="/custom/path/db.sqlite"):
        """Create a test config file."""
        config = ConfigParser()
        config["general"] = {
            "default_provider": "anthropic",
        }
        config["model"] = {
            "recursion_limit": "25",
        }
        config["inference"] = {
            "temperature": "0.2",
            "max_tokens": "4096",
        }
        config["database"] = {
            "enabled": "true" if db_enabled else "false",
            "path": db_path,
        }

        with open(self.config_path, "w") as f:
            config.write(f)

        return self.config_path

    @patch("vmpilot.config.find_config_file")
    def test_database_config_enabled(self, mock_find_config):
        """Test that database configuration is correctly parsed when enabled."""
        # Create config file with database enabled
        config_path = self.create_config(
            db_enabled=True, db_path="/custom/path/db.sqlite"
        )
        mock_find_config.return_value = config_path

        # Reload configuration
        model_config = ModelConfig()

        # Check that database config is correctly loaded
        self.assertTrue(model_config.is_database_enabled())
        self.assertEqual(model_config.database_config.path, "/custom/path/db.sqlite")

    @patch("vmpilot.config.find_config_file")
    def test_database_config_disabled(self, mock_find_config):
        """Test that database configuration is correctly parsed when disabled."""
        # Create config file with database disabled
        config_path = self.create_config(db_enabled=False)
        mock_find_config.return_value = config_path

        # Reload configuration
        model_config = ModelConfig()

        # Check that database config is correctly loaded
        self.assertFalse(model_config.is_database_enabled())

    @patch("vmpilot.config.find_config_file")
    def test_database_config_missing(self, mock_find_config):
        """Test that default database configuration is used when section is missing."""
        # Create config file without database section
        config = ConfigParser()
        config["general"] = {
            "default_provider": "anthropic",
        }
        with open(self.config_path, "w") as f:
            config.write(f)

        mock_find_config.return_value = self.config_path

        # Reload configuration
        model_config = ModelConfig()

        # Check that default database config is used
        self.assertFalse(model_config.is_database_enabled())
        self.assertEqual(model_config.database_config.path, "/app/data/vmpilot.db")


if __name__ == "__main__":
    unittest.main()
