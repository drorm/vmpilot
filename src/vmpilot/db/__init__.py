"""
Database module for VMPilot conversation persistence.
Provides SQLite-based storage for conversations and messages.
"""

from .connection import get_db_connection, initialize_database
from .models import SCHEMA_VERSION

__all__ = ["get_db_connection", "initialize_database", "SCHEMA_VERSION"]
