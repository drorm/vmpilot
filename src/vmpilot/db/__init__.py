"""
SQLite database module for persisting conversations.

This module provides functionality for storing and retrieving 
conversations in a SQLite database to enable conversation persistence
across sessions.
"""

import atexit
import logging

from vmpilot.config import config

from .connection import close_db_connection, get_db_connection
from .crud import ConversationRepository

# Configure logging
logger = logging.getLogger(__name__)

# Register the database connection closure with atexit if DB is enabled
if config.is_database_enabled():
    atexit.register(close_db_connection)
    logger.debug("Registered database connection closure with atexit")
else:
    logger.debug("Database persistence is disabled in configuration")

# NOTE: Database schema management is performed by Alembic migrations. No direct initialization here.

__all__ = [
    "get_db_connection",
    "close_db_connection",
    "ConversationRepository",
]
