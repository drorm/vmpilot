"""
SQLite database module for persisting conversations.

This module provides functionality for storing and retrieving 
conversations in a SQLite database to enable conversation persistence
across sessions.
"""

import atexit
import logging

from vmpilot.config import config

from .connection import close_db_connection, get_db_connection, initialize_db
from .crud import ConversationRepository

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the database when the module is imported
try:
    if config.is_database_enabled():
        logger.debug("Initializing SQLite database for conversation persistence")
        initialize_db()

        # Register the database connection closure with atexit
        # This ensures the connection is closed when the program exits
        atexit.register(close_db_connection)
        logger.debug("Registered database connection closure with atexit")
    else:
        logger.debug("Database persistence is disabled in configuration")
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    # Don't raise the exception - allow the application to continue without database

__all__ = [
    "get_db_connection",
    "initialize_db",
    "close_db_connection",
    "ConversationRepository",
]
