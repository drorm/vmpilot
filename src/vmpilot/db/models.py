"""
Database models and schema definitions for SQLite persistence.

This module defines the database schema for storing conversations, exchanges,
and messages in a SQLite database.
"""

# SQL statements for table creation
SCHEMA_SQL = [
    """
    -- Chats table to track conversation threads
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,               -- chat_id/thread_id
        initial_request TEXT,              -- The first user message that started the chat
        project_root TEXT,                 -- Path to the project directory
        current_issue TEXT,                -- Current issue being worked on (if any)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT                      -- JSON string for additional metadata
    );
    """,
    """
    -- Exchanges table to store complete exchanges
    CREATE TABLE IF NOT EXISTS exchanges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT NOT NULL,
        user_message TEXT NOT NULL,        -- Serialized user message
        assistant_response TEXT,           -- Serialized assistant message
        tool_calls TEXT,                   -- JSON serialized tool calls
        started_at TIMESTAMP NOT NULL,     -- When the exchange started
        completed_at TIMESTAMP,            -- When the exchange completed
        serialized_exchange TEXT,          -- Full serialized Exchange object
        FOREIGN KEY (chat_id) REFERENCES chats(id)
    );
    """,
]
