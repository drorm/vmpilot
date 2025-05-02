# SQLite Persistence Implementation

This document describes the implementation of SQLite persistence for conversation states in VMPilot (Issue #31).

## Overview

We've implemented a database system to persist chat sessions and exchanges so they can be replayed in future sessions. The implementation follows the same pattern as the in-memory storage system but uses SQLite as the backend.

## Implementation Details

### Database Structure

The database consists of two main tables:

1. **chats** - Stores metadata about conversation threads
2. **chat_histories** - Stores the serialized message history and cache information

### Module Structure

We've created the following modules:

1. **db/connection.py** - Manages SQLite database connections
2. **db/models.py** - Defines the database schema
3. **db/crud.py** - Implements the ConversationRepository class for CRUD operations
4. **persistent_memory.py** - Provides the same interface as agent_memory.py but uses the database
5. **unified_memory.py** - Dynamically selects between in-memory and database storage based on configuration

### Configuration

Database persistence can be enabled or disabled in the `config.ini` file:

```ini
[database]
enabled = true
path = /app/data/vmpilot.db
```

### Serialization Strategy

The implementation follows the same pattern as the in-memory approach:

1. Convert the message list to JSON-serializable format
2. Save in the database
3. Fetch from the database
4. Deserialize

## Integration with Existing Code

The integration with the existing code is minimal and non-invasive:

1. We've created a unified interface that can switch between in-memory and database storage
2. Updated imports in relevant files to use the unified interface
3. Added configuration options to enable/disable database persistence

## Usage

The usage pattern remains the same as before:

```python
from vmpilot.unified_memory import (
    save_conversation_state,
    get_conversation_state,
    update_cache_info,
    clear_conversation_state,
)

# Save conversation state
save_conversation_state(thread_id, messages, cache_info)

# Retrieve conversation state
messages, cache_info = get_conversation_state(thread_id)

# Update cache info
update_cache_info(thread_id, new_cache_info)

# Clear conversation state
clear_conversation_state(thread_id)
```

## Testing

Tests have been implemented to verify the functionality:

1. Unit tests for the database module
2. Unit tests for the persistent memory module
3. A manual test script to verify the unified memory implementation

## Next Steps

Potential future enhancements:

1. Add a management interface to view and manage stored conversations
2. Implement database migrations for schema updates
3. Add support for conversation metadata like project context, creation time, etc.
4. Implement conversation export/import functionality