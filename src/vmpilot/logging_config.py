import logging
import os


class StreamContentFilter(logging.Filter):
    """Filter out stream-related log messages from the root logger."""

    def filter(self, record):
        if record.name == "root":
            message = record.getMessage()
            # Filter out 'stream_content:Generator:' messages
            if "stream_content:Generator:" in message:
                return False
            # Filter out 'stream:true:<generator object' messages from pipelines main.py
            if "stream:true:<generator object" in message:
                return False
        return True


def configure_logging():
    """Configure logging with custom filters."""
    # Get log level from environment variable
    log_level = os.environ.get("PYTHONLOGLEVEL", "INFO")

    # Configure basic logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Add filter to root logger to remove 'stream_content:Generator:' messages
    root_logger = logging.getLogger()
    root_logger.addFilter(StreamContentFilter())

    # Set up vmpilot module logger
    vmpilot_logger = logging.getLogger("vmpilot")
    vmpilot_logger.setLevel(getattr(logging, log_level))
