"""
Configuration management for VMPilot providers and models.
Uses configuration from config.ini in the root directory.
"""

import os
import sys
from configparser import ConfigParser
from enum import StrEnum
from typing import Dict, Optional
from pathlib import Path
import logging

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

        if not parser.read(config_path):
            raise ConfigError(f"Failed to read config file at {config_path}")

        # Verify required sections exist
        required_sections = ["general", "model", "inference"]
        missing_sections = [s for s in required_sections if not parser.has_section(s)]
        if missing_sections:
            raise ConfigError(
                f"Missing required config sections: {', '.join(missing_sections)}"
            )

        config_loaded = True
        return parser

    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise ConfigError(f"Failed to load configuration: {str(e)}")


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
    available_models: list[str]
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
            if not config_loaded:
                raise ConfigError("Configuration not properly loaded")

            # Read from config.ini
            default_provider = parser.get("general", "default_provider")
            recursion_limit = parser.getint("model", "recursion_limit")

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
                        default_model=section["default_model"],
                        available_models=section["available_models"].split(","),
                        api_key_path=section["api_key_path"],
                        api_key_env=section["api_key_env"],
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

    def validate_model(self, model: str, provider: Optional[Provider] = None) -> bool:
        """Check if model is valid for specified provider"""
        config = self.get_provider_config(provider)
        return model in config.available_models


# Global configuration instance
config = ModelConfig()

# General configuration
DEFAULT_PROVIDER = parser.get("general", "default_provider")
TOOL_OUTPUT_LINES = parser.getint("general", "tool_output_lines")

# Inference parameters
TEMPERATURE = parser.getfloat("inference", "temperature")
MAX_TOKENS = parser.getint("inference", "max_tokens")
RECURSION_LIMIT = parser.getint("model", "recursion_limit")
