"""
LLM Wrapper for debugging API requests and responses.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

class LLMWrapper:
    """Wraps an LLM client to log all API calls and responses."""
    
    def __init__(self, wrapped_class):
        self.wrapped_class = wrapped_class
        
    def __getattr__(self, attr):
        original_func = getattr(self.wrapped_class, attr)
        
        def wrapper(*args, **kwargs):
            logger.debug(f"LLM API Call: {attr}")
            logger.debug(f"Arguments: {args}")
            logger.debug(f"Keyword Arguments: {kwargs}")
            
            try:
                result = original_func(*args, **kwargs)
                logger.debug(f"API Response: {result}")
                return result
            except Exception as e:
                logger.error(f"API Call Failed: {str(e)}")
                logger.error(f"Function: {attr}")
                logger.error(f"Arguments: {args}, {kwargs}")
                raise
                
        return wrapper

def wrap_llm(llm: Any) -> Any:
    """Wraps an LLM instance to enable API call logging.
    
    Args:
        llm: The LLM instance to wrap (ChatOpenAI, ChatAnthropic, etc.)
        
    Returns:
        The wrapped LLM instance with logging enabled
    """
    # Set debug logging
    logging.getLogger(__name__).setLevel(logging.DEBUG)
    
    # Wrap the client
    llm.client = LLMWrapper(llm.client)
    return llm

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LLMWrapper:
    """Wrapper class to log all LLM API calls and responses"""

    def __init__(self, wrapped_class):
        self.wrapped_class = wrapped_class

    def __getattr__(self, attr):
        original_func = getattr(self.wrapped_class, attr)

        def wrapper(*args, **kwargs):
            logger.debug(f"LLM API Call: {attr}")
            logger.debug(f"Arguments: {args}")
            logger.debug(f"Keyword Arguments: {kwargs}")
            try:
                result = original_func(*args, **kwargs)
                logger.debug(f"API Response: {result}")
                return result
            except Exception as e:
                logger.error(f"API Error in {attr}: {e}")
                logger.error(f"Full API Response: {getattr(e, 'response', None)}")
                raise

        return wrapper


def wrap_llm(llm: Any) -> Any:
    """
    Wrap an LLM instance to enable API request/response logging.

    Args:
        llm: The LLM instance to wrap

    Returns:
        The wrapped LLM instance
    """
    if hasattr(llm, "client"):
        llm.client = LLMWrapper(llm.client)
    return llm
