"""
SQLite connection management for VMPilot.
Provides functions for initializing and accessing the database.
"""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional

from ..config import get_config_value, DATA_DIR, DB_PATH
from .models import CREATE_TABLES_SQL, SCHEMA_VERSION, get_set_schema_version_sql

# Configure logging
logger = logging.getLogger(__name__)

# Global connection object (singleton)
_db_connection: Optional[sqlite3.Connection] = None


def get_db_path() -> Path:
    """
    Get the database file path from configuration.

    Returns:
        Path object pointing to the database file
    """
    # Use DB_PATH from config.py, which already includes a sensible default
    db_path = Path(DB_PATH)

    # Ensure the parent directory exists (DATA_DIR should already be created in config.py)
    os.makedirs(db_path.parent, exist_ok=True)

    logger.debug(f"Using database at: {db_path}")
    return db_path


def get_db_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.
    Uses a singleton pattern to reuse the connection.

    Returns:
        SQLite connection object
    """
    global _db_connection

    if _db_connection is None:
        db_path = get_db_path()

        # Initialize the database if it doesn't exist
        db_exists = db_path.exists()

        # Create the connection with row factory to get dict-like rows
        _db_connection = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False,  # Allow access from multiple threads
        )

        # Configure connection
        _db_connection.row_factory = sqlite3.Row

        # Enable foreign keys
        _db_connection.execute("PRAGMA foreign_keys = ON;")

        # Initialize database if it's new
        if not db_exists:
            initialize_database(_db_connection)
        else:
            # Verify schema version
            verify_schema_version(_db_connection)

    return _db_connection


def initialize_database(conn: sqlite3.Connection) -> None:
    """
    Initialize the database schema.

    Args:
        conn: SQLite connection object
    """
    logger.info("Initializing database schema")

    # Execute all creation statements in a transaction
    with conn:
        for statement in CREATE_TABLES_SQL:
            conn.execute(statement)

        # Set the schema version
        conn.execute(get_set_schema_version_sql(SCHEMA_VERSION))

    logger.info(f"Database initialized with schema version {SCHEMA_VERSION}")


def verify_schema_version(conn: sqlite3.Connection) -> None:
    """
    Verify that the database schema is at the expected version.

    Args:
        conn: SQLite connection object
    """
    try:
        # Check if schema_version table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version';"
        )
        if not cursor.fetchone():
            logger.warning("Schema version table not found. Initializing database.")
            initialize_database(conn)
            return

        # Get the current schema version
        cursor = conn.execute("SELECT version FROM schema_version LIMIT 1;")
        row = cursor.fetchone()

        if not row:
            logger.warning("No schema version found. Setting to current version.")
            conn.execute(get_set_schema_version_sql(SCHEMA_VERSION))
            return

        db_version = row[0]

        if db_version < SCHEMA_VERSION:
            logger.warning(
                f"Database schema version ({db_version}) is older than expected ({SCHEMA_VERSION}). "
                "Migration may be required."
            )
            # Here you would implement migration logic if needed

        elif db_version > SCHEMA_VERSION:
            logger.warning(
                f"Database schema version ({db_version}) is newer than expected ({SCHEMA_VERSION}). "
                "This may cause compatibility issues."
            )

    except Exception as e:
        logger.error(f"Error verifying schema version: {str(e)}")
        # If there's an error, it's safest to reinitialize
        logger.info("Reinitializing database due to schema verification error")
        initialize_database(conn)
