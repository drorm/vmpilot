"""
SQLite connection management for VMPilot.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

from vmpilot.config import config
from vmpilot.db.models import SCHEMA_SQL

# Singleton connection instance
_db_connection: Optional[sqlite3.Connection] = None


def get_db_path() -> Path:
    """
    Get the path to the SQLite database file from config or use default.

    Returns:
        Path: The path to the SQLite database file
    """
    # Default location in the data directory
    default_path = Path("/app/data/vmpilot.db")

    # Check if running locally (not in Docker)
    if not os.path.exists("/app/data"):
        default_path = Path.home() / ".vmpilot" / "vmpilot.db"

    # Get path from config or use default
    db_path_str = config.get("database", "path", fallback=str(default_path))
    db_path = Path(db_path_str)

    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return db_path


def initialize_db() -> None:
    """
    Initialize the database with the required schema.

    Creates tables if they don't exist.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    # Execute each SQL statement in the schema
    for sql in SCHEMA_SQL:
        cursor.execute(sql)

    connection.commit()


def get_db_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection to the SQLite database
    """
    global _db_connection

    if _db_connection is None:
        db_path = get_db_path()
        _db_connection = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,  # Allow access from multiple threads
        )
        _db_connection.row_factory = sqlite3.Row

    return _db_connection
