import logging
import os

class StreamContentFilter(logging.Filter):
    """Filter out stream_content log messages from the root logger."""
    
    def filter(self, record):
        # Return False to filter out messages containing 'stream_content:Generator:'
        if record.name == 'root' and 'stream_content:Generator:' in record.getMessage():
            return False
        return True

def configure_logging():
    """Configure logging with custom filters."""
    # Get log level from environment variable
    log_level = os.environ.get('PYTHONLOGLEVEL', 'INFO')
    
    # Configure basic logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Add filter to root logger to remove 'stream_content:Generator:' messages
    root_logger = logging.getLogger()
    root_logger.addFilter(StreamContentFilter())
    
    # Set up vmpilot module logger
    vmpilot_logger = logging.getLogger("vmpilot")
    vmpilot_logger.setLevel(getattr(logging, log_level))