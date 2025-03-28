import os
from configparser import ConfigParser
from pathlib import Path

import pytest

from vmpilot.config import (
    ConfigError,
    ModelConfig,
    Provider,
    find_config_file,
    load_config,
)


def test_default_config_loading():
    """Test loading the default configuration file"""
    # Should load without raising exceptions
    parser = load_config()
    assert parser is not None
    assert isinstance(parser, ConfigParser)

    # Check required sections exist
    required_sections = ["general", "model", "inference"]
    for section in required_sections:
        assert parser.has_section(section)

    # Verify some key settings
    assert parser.get("general", "default_provider") in [
        "anthropic",
        "openai",
        "google",
    ]
    assert parser.getint("general", "tool_output_lines") > 0


def test_custom_config_path(tmp_path):
    """Test loading a custom configuration file path"""
    # Create a minimal test config
    test_config = tmp_path / "test_config.ini"
    test_config.write_text(
        """
[general]
default_provider = anthropic
tool_output_lines = 10

[model]
recursion_limit = 20

[inference]
temperature = 0.7
max_tokens = 100000
"""
    )

    # Set environment variable to point to test config
    os.environ["VMPILOT_CONFIG"] = str(test_config)

    try:
        config_path = find_config_file()
        assert config_path == test_config

        parser = load_config()
        assert parser.get("general", "default_provider") == "anthropic"
        assert parser.getint("general", "tool_output_lines") == 10
        assert parser.getint("model", "recursion_limit") == 20
    finally:
        # Clean up environment
        del os.environ["VMPILOT_CONFIG"]


def test_missing_config_file(tmp_path):
    """Test handling of missing config file"""
    # Point to non-existent config file
    os.environ["VMPILOT_CONFIG"] = str(tmp_path / "nonexistent.ini")

    try:
        # When config file is missing, load_config should return an empty parser
        parser = load_config()
        assert isinstance(parser, ConfigParser)
        assert len(parser.sections()) == 0
    finally:
        del os.environ["VMPILOT_CONFIG"]


def test_missing_required_sections(tmp_path):
    """Test handling of config file with missing required sections"""
    # Create config missing required sections
    test_config = tmp_path / "incomplete_config.ini"
    test_config.write_text(
        """
[general]
default_provider = anthropic
"""
    )

    os.environ["VMPILOT_CONFIG"] = str(test_config)

    try:
        # When required sections are missing, load_config should return a parser with only the general section
        parser = load_config()
        assert isinstance(parser, ConfigParser)
        assert len(parser.sections()) == 1  # Only general section present
        assert parser.has_section("general")
    finally:
        del os.environ["VMPILOT_CONFIG"]


def test_model_config_initialization(tmp_path):
    """Test ModelConfig initialization with valid config"""
    # Create a test config file
    test_config = tmp_path / "test_config.ini"
    test_config.write_text(
        """
[general]
default_provider = anthropic
tool_output_lines = 15

[model]
recursion_limit = 25

[inference]
temperature = 0.7
max_tokens = 8192

[anthropic]
default_model = claude-2
api_key_path = ~/.config/vmpilot/anthropic.key
api_key_env = ANTHROPIC_API_KEY
beta_flags = foo:bar

[openai]
default_model = gpt-4
api_key_path = ~/.config/vmpilot/openai.key
api_key_env = OPENAI_API_KEY
"""
    )

    # Set environment variable to point to test config
    os.environ["VMPILOT_CONFIG"] = str(test_config)

    try:
        # Force reload of config
        global config_loaded
        config_loaded = False
        model_config = ModelConfig()

        # Check default provider is set
        assert model_config.default_provider in Provider

        # Check provider configs are loaded
        assert len(model_config.providers) > 0

        # Test provider config access
        default_config = model_config.get_provider_config()
        assert default_config.default_model
        assert default_config.api_key_path
        assert default_config.api_key_env
    finally:
        # Clean up environment
        del os.environ["VMPILOT_CONFIG"]
