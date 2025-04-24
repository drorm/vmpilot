"""
Unit tests for database connection shutdown functionality.

Tests the database connection cleanup during application shutdown.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vmpilot.vmpilot import Pipeline


class TestDatabaseShutdown:
    """Test cases for database connection shutdown functionality."""

    @pytest.mark.asyncio
    @patch("vmpilot.db.close_db_connection")
    @patch("vmpilot.vmpilot.logger")
    async def test_pipeline_on_shutdown(self, mock_logger, mock_close_db):
        """Test that on_shutdown closes the database connection."""
        # Create a Pipeline instance
        pipeline = Pipeline()

        # Call the on_shutdown method
        await pipeline.on_shutdown()

        # Verify that close_db_connection was called
        mock_close_db.assert_called_once()
        mock_logger.debug.assert_called_with(
            "Database connection closed during pipeline shutdown"
        )

    @pytest.mark.asyncio
    @patch("vmpilot.db.close_db_connection")
    @patch("vmpilot.vmpilot.logger")
    async def test_pipeline_on_shutdown_with_error(self, mock_logger, mock_close_db):
        """Test handling errors during database connection shutdown."""
        # Set up the mock to raise an exception
        mock_close_db.side_effect = Exception("Connection error")

        # Create a Pipeline instance
        pipeline = Pipeline()

        # Call the on_shutdown method
        await pipeline.on_shutdown()

        # Verify that the error was logged
        mock_logger.error.assert_called_once()
        assert "Error closing database connection" in mock_logger.error.call_args[0][0]


if __name__ == "__main__":
    unittest.main()
