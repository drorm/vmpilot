"""
Configuration management for VMPilot providers and models.
Uses configuration from config.ini in the root directory.
"""

import os
from configparser import ConfigParser
from enum import StrEnum
from typing import Dict, Optional
from pathlib import Path

from pydantic import BaseModel, Field

# Read configuration file
config_path = Path(__file__).parent.parent.parent / "config.ini"
parser = ConfigParser()
parser.read(config_path)


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

# Number of lines to show in tool output before truncating
TOOL_OUTPUT_LINES = parser.getint("general", "tool_output_lines")
