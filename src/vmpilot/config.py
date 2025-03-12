"""
Configuration management for VMPilot providers and models.
Uses configuration from config.ini in the root directory.
"""

import logging
import os
import sys
from configparser import ConfigParser
from enum import StrEnum
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ConfigError(Exception):
    """Configuration related errors"""

    pass


def find_config_file() -> Path:
    """Find the configuration file in multiple possible locations"""
    # Try environment variable first
    if config_env := os.getenv("VMPILOT_CONFIG"):
        return Path(config_env)

    # Try default locations
    possible_paths = [
        Path(__file__).parent / "config.ini",  # Default project structure
        Path.cwd() / "config.ini",  # Current working directory
        Path.home() / ".config" / "vmpilot" / "config.ini",  # User config directory
    ]

    for path in possible_paths:
        if path.exists():
            return path

    raise ConfigError(
        f"Config file not found. Searched in: {', '.join(str(p) for p in possible_paths)}"
    )


# Read configuration file
# Initialize parser at module level
parser = ConfigParser()
config_loaded = False


def load_config():
    """Load the configuration file and return parser"""
    global config_loaded, parser

    try:
        config_path = find_config_file()
        logger.info(f"Using config file at {config_path}")

        # Create a new parser instance to avoid accumulating sections
        parser = ConfigParser()

        if not parser.read(config_path):
            logger.warning(f"Failed to read config file at {config_path}")
            return parser

        # Verify required sections exist
        required_sections = ["general", "model", "inference"]
        missing_sections = [s for s in required_sections if not parser.has_section(s)]
        if missing_sections:
            logger.warning(
                f"Missing required config sections: {', '.join(missing_sections)}"
            )
            # Return parser with only existing sections
            return parser

        config_loaded = True
        return parser

    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        # Return empty parser instead of raising exception
        return ConfigParser()


# Load configuration
try:
    parser = load_config()
except ConfigError as e:
    logger.error(str(e))
    # Don't exit here - let the application handle the error
    parser = ConfigParser()  # Provide empty parser as fallback


class Provider(StrEnum):
    """Supported LLM providers"""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class ProviderConfig(BaseModel):
    """Configuration for a specific provider"""

    default_model: str
    api_key_path: str = Field(description="Default path to API key file")
    api_key_env: str = Field(description="Environment variable name for API key")
    beta_flags: Dict[str, str] = Field(default_factory=dict)
    recursion_limit: int = Field(
        default=25, description="Maximum number of recursive steps the model can take"
    )


class ModelConfig(BaseModel):
    """Global model configuration"""

    providers: Dict[Provider, ProviderConfig] = Field(default_factory=dict)
    default_provider: Provider

    def __init__(self):
        try:
            # Reload config to ensure we have fresh data
            parser = load_config()

            # Read from config.ini
            default_provider = parser.get(
                "general", "default_provider", fallback="anthropic"
            )
            recursion_limit = parser.getint("model", "recursion_limit", fallback=25)

            # Initialize providers
            providers = {}
            for provider in Provider:
                if parser.has_section(provider.value):
                    section = parser[provider.value]
                    beta_flags = {}
                    if "beta_flags" in section:
                        for flag_pair in section["beta_flags"].split(","):
                            key, value = flag_pair.split(":")
                            beta_flags[key] = value

                    providers[provider] = ProviderConfig(
                        default_model=section.get("default_model", ""),
                        api_key_path=section.get("api_key_path", ""),
                        api_key_env=section.get("api_key_env", ""),
                        beta_flags=beta_flags,
                        recursion_limit=recursion_limit,
                    )

            super().__init__(
                providers=providers, default_provider=Provider(default_provider)
            )

        except Exception as e:
            logger.error(f"Failed to initialize model config: {str(e)}")
            # Initialize with empty/default values
            super().__init__(
                providers={}, default_provider=Provider.ANTHROPIC  # Set a default
            )

    def get_provider_config(
        self, provider: Optional[Provider] = None
    ) -> ProviderConfig:
        """Get configuration for specified provider or default provider"""
        if provider is None:
            provider = self.default_provider
        return self.providers[provider]

    def get_default_model(self, provider: Optional[Provider] = None) -> str:
        """Get default model for specified provider"""
        return self.get_provider_config(provider).default_model


# Global configuration instance
config = ModelConfig()

# General configuration
DEFAULT_PROVIDER = parser.get("general", "default_provider")
TOOL_OUTPUT_LINES = parser.getint("general", "tool_output_lines")

# Inference parameters
TEMPERATURE = parser.getfloat("inference", "temperature")
MAX_TOKENS = parser.getint("inference", "max_tokens")
RECURSION_LIMIT = parser.getint("model", "recursion_limit")

# Database configuration
DATA_DIR = os.environ.get(
    "VMPILOT_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"),
)
DB_PATH = os.environ.get("VMPILOT_DB_PATH", os.path.join(DATA_DIR, "vmpilot.db"))

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)


def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """
    Get a configuration value from the config file.

    Args:
        section: The section in the config file
        key: The key in the section
        default: Default value if the key doesn't exist

    Returns:
        The configuration value or the default
    """
    try:
        if section in parser and key in parser[section]:
            return parser[section][key]
        return default
    except Exception:
        return default
