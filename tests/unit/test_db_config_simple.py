"""
Simple tests for database configuration.
"""

import unittest
from unittest.mock import patch

from vmpilot.config import DatabaseConfig, ModelConfig


class TestDatabaseConfig(unittest.TestCase):
    """Test cases for database configuration."""

    def test_database_config_defaults(self):
        """Test that DatabaseConfig has expected defaults."""
        config = DatabaseConfig()
        self.assertFalse(config.enabled, "Database should be disabled by default")
        self.assertEqual(
            config.path,
            "/app/data/vmpilot.db",
            "Default path should be /app/data/vmpilot.db",
        )

    def test_database_config_custom_values(self):
        """Test that DatabaseConfig can be initialized with custom values."""
        config = DatabaseConfig(enabled=True, path="/custom/path/db.sqlite")
        self.assertTrue(config.enabled, "Custom enabled value not applied")
        self.assertEqual(
            config.path, "/custom/path/db.sqlite", "Custom path not applied"
        )

    def test_is_database_enabled(self):
        """Test the is_database_enabled method."""
        # Create a config with database enabled
        config = ModelConfig()

        # Test with database enabled
        with patch.object(config, "database_config", DatabaseConfig(enabled=True)):
            self.assertTrue(config.is_database_enabled(), "Database should be enabled")

        # Test with database disabled
        with patch.object(config, "database_config", DatabaseConfig(enabled=False)):
            self.assertFalse(
                config.is_database_enabled(), "Database should be disabled"
            )


if __name__ == "__main__":
    unittest.main()
