"""Tests for validating config.ini values and their constraints.

This module focuses on testing the actual values and constraints of the
configuration file, complementing the config file loading tests in test_config.py.
"""

import pytest
from vmpilot.config import load_config, ConfigError


@pytest.fixture
def config():
    """Fixture to load the configuration for testing."""
    return load_config()


class TestGeneralSection:
    """Tests for the [general] section of the config file."""

    def test_default_provider_valid_values(self, config):
        """Test that default_provider is one of the allowed values."""
        allowed_providers = {'anthropic', 'openai'}
        assert config['general']['default_provider'] in allowed_providers, \
            f"default_provider must be one of {allowed_providers}"

    def test_tool_output_lines_valid(self, config):
        """Test that tool_output_lines accepts valid positive integers."""
        tool_lines = int(config['general']['tool_output_lines'])
        assert tool_lines > 0, "tool_output_lines must be positive"
        assert isinstance(tool_lines, int), "tool_output_lines must be an integer"

    def test_tool_output_lines_exists(self, config):
        """Test that tool_output_lines exists in config."""
        assert 'tool_output_lines' in config['general'], \
            "tool_output_lines must be defined in config"


class TestModelSection:
    """Tests for the [model] section of the config file."""

    def test_recursion_limit_exists(self, config):
        """Test that recursion_limit is present in config."""
        assert 'recursion_limit' in config['model'], \
            "recursion_limit must be defined in config"

    def test_recursion_limit_positive(self, config):
        """Test that recursion_limit is a positive integer."""
        limit = int(config['model']['recursion_limit'])
        assert isinstance(limit, int), \
            "recursion_limit must be an integer"
        assert limit > 0, \
            "recursion_limit must be positive"

    def test_recursion_limit_range(self, config):
        """Test that recursion_limit is within reasonable range."""
        limit = int(config['model']['recursion_limit'])
        assert 0 < limit <= 100, \
            "recursion_limit must be between 1 and 100"
