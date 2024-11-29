#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export ANTHROPIC_API_KEY=`cat ~/.anthropic/api_key`

cd "$SCRIPT_DIR/.."
PYTHONPATH="$(pwd)" python3 src/vmpilot/cli.py "$@"
