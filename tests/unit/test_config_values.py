"""Tests for validating config.ini values and their constraints."""

import os
from configparser import ConfigParser
from pathlib import Path

import pytest

from vmpilot.config import ConfigError, load_config


@pytest.fixture
def config():
    """Fixture to load the configuration for testing."""
    return load_config()


class TestGeneralSection:
    """Tests for the [general] section of the config file."""

    def test_default_provider_valid_values(self, config):
        """Test that default_provider is one of the allowed values."""
        allowed_providers = {"anthropic", "openai"}
        assert (
            config["general"]["default_provider"] in allowed_providers
        ), f"default_provider must be one of {allowed_providers}"

    def test_tool_output_lines_valid(self, config):
        """Test that tool_output_lines accepts valid positive integers."""
        tool_lines = int(config["general"]["tool_output_lines"])
        assert tool_lines > 0, "tool_output_lines must be positive"
        assert isinstance(tool_lines, int), "tool_output_lines must be an integer"

    def test_tool_output_lines_exists(self, config):
        """Test that tool_output_lines exists in config."""
        assert (
            "tool_output_lines" in config["general"]
        ), "tool_output_lines must be defined in config"


class TestModelSection:
    """Tests for the [model] section of the config file."""

    def test_recursion_limit_exists(self, config):
        """Test that recursion_limit is present in config."""
        assert (
            "recursion_limit" in config["model"]
        ), "recursion_limit must be defined in config"

    def test_recursion_limit_positive(self, config):
        """Test that recursion_limit is a positive integer."""
        limit = int(config["model"]["recursion_limit"])
        assert isinstance(limit, int), "recursion_limit must be an integer"
        assert limit > 0, "recursion_limit must be positive"

    def test_recursion_limit_range(self, config):
        """Test that recursion_limit is within reasonable range."""
        limit = int(config["model"]["recursion_limit"])
        assert 0 < limit <= 100, "recursion_limit must be between 1 and 100"


class TestInferenceSection:
    """Tests for the [inference] section of the config file."""

    def test_temperature_exists(self, config):
        """Test that temperature setting exists."""
        assert (
            "temperature" in config["inference"]
        ), "temperature must be defined in config"

    def test_temperature_range(self, config):
        """Test that temperature is a float between 0.0 and 1.0"""
        temp = float(config["inference"]["temperature"])
        assert 0.0 <= temp <= 1.0, "temperature must be between 0.0 and 1.0"

    def test_max_tokens_exists(self, config):
        """Test that max_tokens setting exists."""
        assert (
            "max_tokens" in config["inference"]
        ), "max_tokens must be defined in config"

    def test_max_tokens_positive(self, config):
        """Test that max_tokens is a positive integer"""
        tokens = int(config["inference"]["max_tokens"])
        assert tokens > 0, "max_tokens must be positive"
        assert isinstance(tokens, int), "max_tokens must be an integer"


class TestProviderConfigurations:
    """Tests for provider-specific configurations."""

    def test_api_key_env_exists(self, config):
        """Test that API key environment variables are defined."""
        for provider in ["anthropic", "openai"]:
            assert (
                "api_key_env" in config[provider]
            ), f"{provider} api_key_env must be defined"

    def test_api_key_env_uppercase(self, config):
        """Test that API key environment variables are uppercase"""
        for provider in ["anthropic", "openai"]:
            env_var = config[provider]["api_key_env"]
            assert env_var.isupper(), f"{provider} api_key_env must be uppercase"

    def test_default_model_exists(self, config):
        """Test that default models are defined."""
        for provider in ["anthropic", "openai"]:
            assert (
                "default_model" in config[provider]
            ), f"{provider} default_model must be defined"

    def test_default_model_not_empty(self, config):
        """Test that default models are specified"""
        for provider in ["anthropic", "openai"]:
            assert config[provider][
                "default_model"
            ].strip(), f"{provider} default_model cannot be empty"

    def test_api_key_path_exists(self, config):
        """Test that API key paths are defined"""
        for provider in ["anthropic", "openai"]:
            assert (
                "api_key_path" in config[provider]
            ), f"{provider} api_key_path must be defined"

    def test_api_key_path_not_empty(self, config):
        """Test that API key paths are specified"""
        for provider in ["anthropic", "openai"]:
            assert config[provider][
                "api_key_path"
            ].strip(), f"{provider} api_key_path cannot be empty"


class TestPipelineSection:
    """Tests for the [pipeline] section of the config file."""

    def test_pipeline_section_exists(self, config):
        """Test that pipeline section exists"""
        assert "pipeline" in config, "pipeline section must exist in config"

    def test_pipeline_name_exists(self, config):
        """Test that pipeline name is defined"""
        assert "name" in config["pipeline"], "pipeline name must be defined"

    def test_pipeline_name_not_empty(self, config):
        """Test that pipeline name is not empty"""
        assert config["pipeline"]["name"].strip(), "pipeline name cannot be empty"

    def test_pipeline_id_exists(self, config):
        """Test that pipeline ID is defined"""
        assert "id" in config["pipeline"], "pipeline ID must be defined"

    def test_pipeline_id_alphanumeric(self, config):
        """Test that pipeline ID contains only alphanumeric characters"""
        pipeline_id = config["pipeline"]["id"]
        assert pipeline_id.isalnum(), "pipeline ID must be alphanumeric"


class TestFilePaths:
    """Tests for validating file paths in configuration."""

    def test_api_key_path_exists(self, config):
        """Test that API key paths are specified and not empty."""
        for provider in ["anthropic", "openai"]:
            path = config[provider]["api_key_path"]
            assert path.strip(), f"{provider} api_key_path cannot be empty"

    def test_api_key_path_expansion(self, config):
        """Test that ~ in API key paths can be expanded."""
        for provider in ["anthropic", "openai"]:
            path = config[provider]["api_key_path"]
            if "~" in path:
                expanded = os.path.expanduser(path)
                assert expanded != path, f"{provider} api_key_path ~ expansion failed"
                assert not expanded.startswith(
                    "~"
                ), f"{provider} api_key_path expansion incomplete"

    def test_api_key_path_absolute(self, config):
        """Test that API key paths are absolute or can be made absolute."""
        for provider in ["anthropic", "openai"]:
            path = config[provider]["api_key_path"]
            if "~" in path:
                path = os.path.expanduser(path)
            absolute_path = os.path.abspath(path)
            assert os.path.isabs(
                absolute_path
            ), f"{provider} api_key_path must be absolute"

    def test_api_key_path_parent_exists(self, config):
        """Test that parent directory of API key path exists."""
        for provider in ["anthropic", "openai"]:
            path = config[provider]["api_key_path"]
            if "~" in path:
                path = os.path.expanduser(path)
            parent_dir = os.path.dirname(os.path.abspath(path))
            assert os.path.exists(
                parent_dir
            ), f"Parent directory for {provider} api_key_path must exist"


class TestConfigurationStructure:
    """Tests for overall configuration file structure."""

    def test_required_sections_present(self, config):
        """Test that all required sections are present"""
        required_sections = [
            "general",
            "model",
            "inference",
            "anthropic",
            "openai",
            "pipeline",
        ]
        for section in required_sections:
            assert (
                section in config.sections()
            ), f"Required section '{section}' is missing"

    def test_no_extra_sections(self, config):
        """Test that there are no unexpected sections"""
        allowed_sections = {
            "general",
            "model",
            "inference",
            "anthropic",
            "openai",
            "pipeline",
        }
        for section in config.sections():
            assert section in allowed_sections, f"Unexpected section '{section}' found"

    def test_section_not_empty(self, config):
        """Test that no section is empty"""
        for section in config.sections():
            assert len(config[section]) > 0, f"Section '{section}' cannot be empty"

    def test_no_duplicate_sections(self, config):
        """Test that there are no duplicate sections"""
        sections = config.sections()
        assert len(sections) == len(set(sections)), "Duplicate sections found in config"
