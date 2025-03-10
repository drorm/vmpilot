"""
Database models and schema definitions for VMPilot.
"""

# Schema version for migration management
SCHEMA_VERSION = 1

# SQL statements for creating the database schema
CREATE_TABLES_SQL = [
    """
    -- Schema version table for managing migrations
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    -- Conversations table to track conversation threads
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY, -- chat_id from the UI
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT  -- JSON string for additional metadata
    );
    """,
    """
    -- Messages table to store individual messages in conversations
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT,
        role TEXT NOT NULL,  -- 'user', 'assistant', 'system'
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        message_id TEXT,  -- Original message ID if available
        metadata TEXT,  -- JSON string for tool calls, etc.
        FOREIGN KEY (conversation_id) REFERENCES chats(id)
    );
    """,
]


# Function to get SQL for setting the schema version
def get_set_schema_version_sql(version: int) -> str:
    """
    Get SQL to set the schema version.

    Args:
        version: The schema version to set

    Returns:
        SQL string for setting the schema version
    """
    return f"""
    INSERT OR REPLACE INTO schema_version (version) VALUES ({version});
    """
