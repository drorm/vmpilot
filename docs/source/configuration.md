# Configuration Guide

## Overview
VMPilot uses a flexible configuration system that supports multiple locations for config files and various settings for LLM providers and model parameters.

## Configuration File Locations
VMPilot looks for configuration in the following locations (in order):
1. Path specified in VMPILOT_CONFIG environment variable
2. ./config.ini in the project directory
3. config.ini in the current working directory
4. ~/.config/vmpilot/config.ini

## Configuration File Structure
The configuration file (config.ini) should contain the following sections:

### [general]
- default_provider: The default LLM provider to use (anthropic or openai)
- tool_output_lines: Number of lines to show in tool output

### [model]
- recursion_limit: Maximum number of recursive steps the model can take

### [inference]
- temperature: Model temperature setting
- max_tokens: Maximum tokens for model responses

### [anthropic] / [openai]
Provider-specific settings:
- default_model: Default model to use for this provider
- api_key_path: Path to API key file
- api_key_env: Environment variable name for API key
- beta_flags: Optional comma-separated key:value pairs for beta features

## Example Configuration
```ini
[general]
default_provider = anthropic
tool_output_lines = 15

[model]
recursion_limit = 25

[inference]
temperature = 0.7
max_tokens = 2000

[anthropic]
default_model = claude-2
api_key_path = ~/.anthropic_key
api_key_env = ANTHROPIC_API_KEY

[openai]
default_model = gpt-4
api_key_path = ~/.openai_key
api_key_env = OPENAI_API_KEY
```

## Environment Variables
- VMPILOT_CONFIG: Optional path to configuration file
- Provider-specific API key variables (as specified in config.ini)