"""
SQLite connection management for VMPilot.
"""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional

from vmpilot.config import config
from vmpilot.db.models import SCHEMA_SQL

# Create a logger instance without modifying the root logger configuration
logger = logging.getLogger(__name__)

# Singleton connection instance
_db_connection: Optional[sqlite3.Connection] = None


def close_db_connection() -> None:
    """
    Close the database connection if it's open.
    This should be called when the application is shutting down.
    """
    global _db_connection
    if _db_connection is not None:
        try:
            logger.info("Closing database connection")
            _db_connection.close()
            _db_connection = None
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")


def get_db_path() -> Path:
    """
    Get the path to the SQLite database file from config or use default.

    Returns:
        Path: The path to the SQLite database file
    """
    # Default location in the data directory
    default_path = Path("/app/data/vmpilot.db")

    # Check if running locally (not in Docker) or if /app/data is not accessible
    if not os.path.exists("/app/data"):
        default_path = Path.home() / ".vmpilot" / "vmpilot.db"

    # Get path from config
    if hasattr(config, "database_config"):
        db_path_str = config.database_config.path
    else:
        db_path_str = str(default_path)
    logger.info(f"Using database path: {db_path_str}")

    # Expand user directory if needed
    db_path = Path(os.path.expanduser(db_path_str))

    try:
        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except (PermissionError, FileNotFoundError):
        # If we can't create the directory (e.g., in CI environment),
        # fall back to user's home directory
        logger.warning(
            f"Could not create directory {db_path.parent}, falling back to home directory"
        )
        db_path = Path.home() / ".vmpilot" / "vmpilot.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

    return db_path


def initialize_db() -> None:
    """
    Initialize the database with the required schema.

    Creates tables if they don't exist.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    # Execute each SQL statement in the schema using executescript
    # which allows multiple statements to be executed at once
    for sql in SCHEMA_SQL:
        cursor.executescript(sql)

    connection.commit()


def update_schema() -> None:
    """
    Update the database schema for existing databases.

    This function checks for missing tables and creates them if needed.
    It should be called during application startup to ensure the database
    schema is up to date.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Check if exchanges table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='exchanges'"
        )
        if not cursor.fetchone():
            # Create exchanges table if it doesn't exist
            cursor.executescript(
                """
            CREATE TABLE IF NOT EXISTS exchanges (
                exchange_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                model TEXT NOT NULL,               -- Model used for the exchange
                request TEXT,
                cost JSON,
                start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            )
            connection.commit()
            logger.info("Created exchanges table in existing database")
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")


def get_db_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection to the SQLite database
    """
    global _db_connection

    if _db_connection is None:
        db_path = get_db_path()

        # Check if the database file exists
        db_exists = db_path.exists()

        # Create connection
        _db_connection = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,  # Allow access from multiple threads
        )
        _db_connection.row_factory = sqlite3.Row

        # Initialize database if it's a new database
        if not db_exists:
            initialize_db()
        else:
            # Update schema for existing database
            update_schema()

    return _db_connection
