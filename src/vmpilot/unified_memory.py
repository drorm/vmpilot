"""
Unified conversation state manager for VMPilot.
This module provides a single interface that can use either in-memory or database storage.
"""

import logging

from vmpilot.config import config

# Configure logging
logger = logging.getLogger(__name__)

# Determine which implementation to use based on config
use_database = True
try:
    use_database = config.is_database_enabled()
    logger.debug(f"Database persistence enabled: {use_database}")
except Exception as e:
    logger.warning(
        f"Error checking database configuration, defaulting to sqlite-memory storage: {e}"
    )
if use_database:
    logger.info("Using database storage for conversation state")
    from vmpilot.persistent_memory import (
        clear_conversation_state,
        get_conversation_state,
        save_conversation_state,
        update_cache_info,
    )
else:
    logger.info("Using in-memory storage for conversation state")
    from vmpilot.agent_memory import (
        clear_conversation_state,
        get_conversation_state,
        save_conversation_state,
        update_cache_info,
    )

__all__ = [
    "save_conversation_state",
    "get_conversation_state",
    "update_cache_info",
    "clear_conversation_state",
]
