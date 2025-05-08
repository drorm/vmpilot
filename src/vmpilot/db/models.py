"""
Database models and schema definitions for SQLite persistence.

This module defines the database schema for storing chats
in the SQLite database.
"""

# SQL statements for table creation
SCHEMA_SQL = [
    """
    -- Chats table to track conversation threads
    CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT PRIMARY KEY,          -- chat_id/thread_id
        initial_request TEXT,              -- The first user message that started the chat
        project_root TEXT,                 -- Path to the project directory, if any
        messages TEXT NOT NULL,            -- JSON serialized message history
        cache_info TEXT NOT NULL,          -- JSON serialized cache information
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS exchanges (
        exchange_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique identifier for each exchange
        chat_id TEXT NOT NULL,             -- Foreign key to chats table
        request TEXT,                      -- Truncated user request
        cost JSON,                         -- JSON serialized cost information
        start TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Start time of the exchange
        end TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- End time of the exchange
    );
    """
]
