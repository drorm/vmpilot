"""
SQLite database module for persisting conversations.

This module provides functionality for storing and retrieving 
conversations in a SQLite database to enable conversation persistence
across sessions.
"""

import logging

from vmpilot.config import config

from .connection import get_db_connection, initialize_db
from .crud import ConversationRepository

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the database when the module is imported
try:
    if hasattr(config, "database_config") and config.database_config.enabled:
        logger.info("Initializing SQLite database for conversation persistence")
        initialize_db()
        logger.info("Database initialization complete")
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    # Don't raise the exception - allow the application to continue without database

__all__ = ["get_db_connection", "initialize_db", "ConversationRepository"]
