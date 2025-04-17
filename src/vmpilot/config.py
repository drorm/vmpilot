"""
Configuration management for VMPilot providers and models.
Uses configuration from config.ini in the root directory.
"""

import logging
import os
import sys
from configparser import ConfigParser
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
# Don't set the level here - it will inherit from the root logger


class ConfigError(Exception):
    """Configuration related errors"""

    pass


class CommitMessageStyle(str, Enum):
    """Enum for Git commit message styles."""

    SHORT = "short"
    DETAILED = "detailed"
    BULLET_POINTS = "bullet_points"


class PricingDisplay(str, Enum):
    """Enum for pricing display options."""

    DISABLED = "disabled"
    TOTAL_ONLY = "total_only"
    DETAILED = "detailed"


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
    GOOGLE = "google"


class ModelPricing(BaseModel):
    """Model pricing information."""

    input_price: float = 0.0
    output_price: float = 0.0
    cache_creation_price: float = 0.0
    cache_read_price: float = 0.0


class ProviderConfig(BaseModel):
    """Configuration for a specific provider"""

    default_model: str
    api_key_path: str = Field(description="Default path to API key file")
    api_key_env: str = Field(description="Environment variable name for API key")
    beta_flags: Dict[str, str] = Field(default_factory=dict)
    recursion_limit: int = Field(
        default=25, description="Maximum number of recursive steps the model can take"
    )


class GitConfig(BaseModel):
    """Git tracking configuration"""

    enabled: bool = Field(default=False, description="Enable Git tracking")
    auto_commit: bool = Field(default=True, description="Auto-commit changes")
    commit_message_style: CommitMessageStyle = Field(
        default=CommitMessageStyle.DETAILED, description="Commit message style"
    )
    model: str = Field(
        default="gpt-3.5-turbo", description="Model for commit message generation"
    )
    provider: Provider = Field(
        default=Provider.OPENAI, description="Provider for commit message generation"
    )
    temperature: float = Field(
        default=0.2, description="Temperature for commit message generation"
    )
    dirty_repo_action: str = Field(
        default="stop",
        description="What to do when repository is dirty (stop, stash)",
    )
    author: str = Field(
        default="VMPilot <vmpilot@example.com>",
        description="Author name and email for Git commits",
    )
    commit_prefix: str = Field(
        default="[VMPilot]", description="Prefix for commit messages"
    )


class ModelConfig(BaseModel):
    """Global model configuration"""

    providers: Dict[Provider, ProviderConfig] = Field(default_factory=dict)
    default_provider: Provider
    git_config: GitConfig = Field(default_factory=GitConfig)
    pricing: Dict[Provider, ModelPricing] = Field(default_factory=dict)
    pricing_display: PricingDisplay = Field(default=PricingDisplay.DETAILED)

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

            # Initialize Git configuration
            git_config = None
            if parser.has_section("git"):
                git_section = parser["git"]
                git_config = GitConfig(
                    enabled=git_section.getboolean("enabled", fallback=False),
                    auto_commit=git_section.getboolean("auto_commit", fallback=True),
                    commit_message_style=CommitMessageStyle(
                        git_section.get("commit_message_style", fallback="detailed")
                    ),
                    model=git_section.get("model", fallback="gpt-3.5-turbo"),
                    provider=Provider(git_section.get("provider", fallback="openai")),
                    temperature=git_section.getfloat("temperature", fallback=0.2),
                    dirty_repo_action=git_section.get(
                        "dirty_repo_action", fallback="stop"
                    ),
                    commit_prefix=git_section.get(
                        "commit_prefix", fallback="[VMPilot]"
                    ),
                    author=git_section.get(
                        "author", fallback="VMPilot <vmpilot@example.com>"
                    ),
                )

            # Initialize pricing information
            pricing = {}
            if parser.has_section("pricing"):
                pricing_section = parser["pricing"]

                # Claude pricing
                claude_pricing = ModelPricing(
                    input_price=pricing_section.getfloat(
                        "claude_input_price", fallback=3.00
                    ),
                    output_price=pricing_section.getfloat(
                        "claude_output_price", fallback=15.00
                    ),
                    cache_creation_price=pricing_section.getfloat(
                        "claude_cache_creation_price", fallback=3.75
                    ),
                    cache_read_price=pricing_section.getfloat(
                        "claude_cache_read_price", fallback=0.30
                    ),
                )
                pricing[Provider.ANTHROPIC] = claude_pricing

                # Log the loaded pricing information
                logger.debug(
                    f"Loaded Claude pricing: input={claude_pricing.input_price}, output={claude_pricing.output_price}, "
                    f"cache_creation={claude_pricing.cache_creation_price}, cache_read={claude_pricing.cache_read_price}"
                )

                # Add OpenAI pricing if/when available

            # Get pricing display option from config
            pricing_display_str = parser.get(
                "general", "pricing_display", fallback="detailed"
            )
            try:
                pricing_display = PricingDisplay(pricing_display_str.lower())
            except ValueError:
                pricing_display = PricingDisplay.DETAILED
                logger.warning(
                    f"Invalid pricing_display value: {pricing_display_str}. Using 'detailed' instead."
                )

            super().__init__(
                providers=providers,
                default_provider=Provider(default_provider),
                git_config=git_config or GitConfig(),
                pricing=pricing,
                pricing_display=pricing_display,
            )

        except Exception as e:
            logger.error(f"Failed to initialize model config: {str(e)}")
            # Initialize with empty/default values
            super().__init__(
                providers={},
                default_provider=Provider.ANTHROPIC,  # Set a default
                git_config=GitConfig(),
                pricing={},  # Empty pricing dictionary
                pricing_display=PricingDisplay.DETAILED,  # Default to detailed display
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

    def get_api_key(self, provider: Optional[Provider] = None) -> str:
        """Get API key for the specified provider.

        Args:
            provider: The provider to get the API key for. If None, uses the default provider.

        Returns:
            The API key as a string.

        Raises:
            ConfigError: If the API key cannot be found or accessed.
        """
        if provider is None:
            provider = self.default_provider

        provider_config = self.get_provider_config(provider)

        # Try environment variable first
        if provider_config.api_key_env and os.environ.get(provider_config.api_key_env):
            return os.environ.get(provider_config.api_key_env, "")

        # Then try key file
        if provider_config.api_key_path:
            key_path = os.path.expanduser(provider_config.api_key_path)
            if os.path.exists(key_path):
                try:
                    with open(key_path, "r") as f:
                        return f.read().strip()
                except Exception as e:
                    raise ConfigError(
                        f"Failed to read API key from {key_path}: {str(e)}"
                    )

        raise ConfigError(
            f"No API key found for provider {provider}. Set environment variable {provider_config.api_key_env} or create key file at {provider_config.api_key_path}"
        )

    def get_pricing(self, provider: Optional[Provider] = None) -> ModelPricing:
        """Get pricing information for the specified provider.

        Args:
            provider: Provider to get pricing for, or None for default provider

        Returns:
            ModelPricing object with pricing information
        """
        if provider is None:
            provider = self.default_provider

        if provider in self.pricing:
            return self.pricing[provider]

        # Return empty pricing if not found
        return ModelPricing()

    def get_pricing_display(self) -> PricingDisplay:
        """Get the current pricing display setting.

        Returns:
            PricingDisplay enum indicating how pricing information should be displayed
        """
        return self.pricing_display


# Global configuration instance
config = ModelConfig()

# General configuration
DEFAULT_PROVIDER = parser.get("general", "default_provider")
TOOL_OUTPUT_LINES = parser.getint("general", "tool_output_lines")
DEFAULT_PROJECT = os.path.expanduser(
    parser.get("general", "default_project", fallback="~/vmpilot")
)

# Inference parameters
TEMPERATURE = parser.getfloat("inference", "temperature")
MAX_TOKENS = parser.getint("inference", "max_tokens")
RECURSION_LIMIT = parser.getint("model", "recursion_limit")
