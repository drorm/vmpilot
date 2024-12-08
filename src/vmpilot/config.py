"""
Configuration management for VMPilot providers and models.
"""

from enum import StrEnum
from typing import Dict, Optional

from pydantic import BaseModel, Field


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
    default_provider: Provider = Provider.ANTHROPIC

    def __init__(self):
        super().__init__()
        self.providers = {
            Provider.ANTHROPIC: ProviderConfig(
                default_model="claude-3-5-sonnet-20241022",
                available_models=[
                    "claude-3-5-sonnet-20241022",
                    "claude-3-opus-20240229",
                ],
                api_key_path="~/.anthropic/api_key",
                api_key_env="ANTHROPIC_API_KEY",
                beta_flags={"computer-use-2024-10-22": "true"},
                recursion_limit=25,
            ),
            Provider.OPENAI: ProviderConfig(
                default_model="gpt-4o",
                available_models=["gpt-4o", "gpt-4"],
                api_key_path="~/.openai",
                api_key_env="OPENAI_API_KEY",
                recursion_limit=25,
            ),
        }

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
