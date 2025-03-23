#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Only set Anthropic API key if not already set in environment
if [ -z "$ANTHROPIC_API_KEY" ]; then
    if [ -f ~/.anthropic/api_key ]; then
        export ANTHROPIC_API_KEY=`cat ~/.anthropic/api_key`
    else
        echo "Error: No API key provided and ~/.anthropic/api_key not found" >&2
        exit 1
    fi
fi

export OPENAI_API_KEY=`cat ~/.openai`
cd "$SCRIPT_DIR/.."

# Set Python logging level to INFO before running the CLI
# This ensures log messages from imports are captured
export PYTHONPATH="$(pwd)"
export PYTHONLOGLEVEL=INFO
python3 src/vmpilot/cli.py "$@"
echo
