# VMPilot Configuration Guide

## Overview
VMPilot features a flexible configuration system that allows you to customize your environment, LLM providers, and model parameters. This guide explains all available configuration options and how to set them up.

## Applying Configuration Changes
After modifying the `config.ini` file, you must restart the VMPilot server for the changes to take effect.
## Docker Install: Configuration File Location
For Docker installations, assuming you are using the default volume setup, the configuration file is located at `/var/lib/docker/volumes/vmpilot_config/_data/config.ini`

To apply changes, restart the VMPilot container:
```bash
docker exec vmpilot supervisorctl restart vmpilot
```


## Manual Install: Configuration File Priority
VMPilot searches for configuration files in the following order:

1. Custom path specified in `VMPILOT_CONFIG` environment variable
2. `./config.ini` in the project directory
3. `config.ini` in the current working directory
4. `~/.config/vmpilot/config.ini`

The first configuration file found will be used.

To apply changes, restart the VMPilot server:
```bash
$MVPILOT_HOME/bin/run.sh
```

## Configuration Sections
The `config.ini` file is organized into the following sections:

### General Settings [general]
| Setting | Description | Default |
|---------|-------------|---------|
| default_provider | Primary LLM provider (anthropic/openai) | anthropic |
| default_project | Default project directory for git operations and file access | ~/vmpilot |
| tool_output_lines | Number of lines shown in tool output | 15 |

### Model Settings [model]
| Setting | Description | Default |
|---------|-------------|---------|
| recursion_limit | Maximum recursive steps allowed | 25 |

### Inference Settings [inference]
| Setting | Description | Default |
|---------|-------------|---------|
| temperature | Model creativity (0.0-1.0) | 0.7 |
| max_tokens | Maximum response length | 2000 |

### Provider Settings [anthropic] / [openai]
| Setting | Description | Example |
|---------|-------------|---------|
| default_model | Default model name | claude-3.5 Sonnet |
| api_key_path | Path to API key file | ~/.anthropic_key |
| api_key_env | API key environment variable | ANTHROPIC_API_KEY |
| beta_flags | Optional beta features (key:value pairs) | feature1:on,feature2:off |

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
