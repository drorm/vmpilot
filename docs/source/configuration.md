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

### Git Settings [git]
| Setting | Description | Default |
|---------|-------------|---------|
| enabled | Enable or disable Git tracking | true |
| dirty_repo_action | Action when repository has uncommitted changes (stop, stash) | stash |
| auto_commit | Automatically commit changes after each exchange | true |
| commit_message_style | Style of generated commit messages (short, detailed, bullet_points) | bullet_points |
| model | Model used for commit message generation | claude-3-7-sonnet-latest |
| provider | Provider for commit message generation (anthropic, openai) | anthropic |
| temperature | Temperature for commit message generation (0.0-1.0) | 0.7 |
| commit_prefix | Prefix added to all commit messages | [VMPilot] |
| author | Author name and email for Git commits | VMPilot <vmpilot@example.com> |

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
default_model = claude-3-7-sonnet-latest
api_key_path = ~/.anthropic/api_key
api_key_env = ANTHROPIC_API_KEY
beta_flags = computer-use-2024-10-22:true

[openai]
default_model = o3-mini
api_key_path = ~/.openai
api_key_env = OPENAI_API_KEY

[git]
enabled = true
dirty_repo_action = stash
auto_commit = true
commit_message_style = bullet_points
model = claude-3-7-sonnet-latest
provider = anthropic
temperature = 0.7
commit_prefix = [VMPilot]
author = VMPilot <vmpilot@example.com>
```

## Environment Variables
- VMPILOT_CONFIG: Optional path to configuration file
- Provider-specific API key variables (as specified in config.ini)
