"""
Unified conversation state manager for VMPilot.
This module provides a single interface that can use either in-memory or database storage.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import BaseMessage

from vmpilot.config import config

# Configure logging
logger = logging.getLogger(__name__)

# Determine which implementation to use based on config
try:
    use_database = getattr(config, "database", {}).get("enabled", False)
    logger.info(f"Database enabled: {use_database}")
except (AttributeError, KeyError):
    logger.warning("Database configuration not found, defaulting to in-memory storage.")
    use_database = False

use_database = True  # hardcode for testing
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
