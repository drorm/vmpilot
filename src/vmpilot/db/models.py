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
    """
]

""" Old schema
-- Chats table to track conversation threads
CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,               -- chat_id/thread_id
    initial_request TEXT,              -- The first user message that started the chat
    project_root TEXT,                 -- Path to the project directory, if any
    current_issue TEXT,                -- Current issue being worked on (if any)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT                      -- JSON string for additional metadata
);

-- Chat histories table to store complete conversation histories
CREATE TABLE IF NOT EXISTS chat_histories (
    chat_id TEXT NOT NULL,             -- Foreign key to chats table
    messages TEXT NOT NULL,            -- JSON serialized message history
    cache_info TEXT NOT NULL,          -- JSON serialized cache information
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);
"""
