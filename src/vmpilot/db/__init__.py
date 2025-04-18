"""
SQLite database module for persisting conversations.

This module provides functionality for storing and retrieving 
conversations in a SQLite database to enable conversation persistence
across sessions.
"""

from .connection import get_db_connection, initialize_db
from .crud import ConversationRepository

__all__ = ["get_db_connection", "initialize_db", "ConversationRepository"]
