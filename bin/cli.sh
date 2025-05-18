#!/bin/bash

# Function to show usage information
show_usage() {
    echo "Usage: cli.sh [OPTIONS] COMMAND"
    echo
    echo "Options:"
    echo "  -c, --chat [ID]       Enable chat mode with optional chat ID"
    echo "  -f, --file FILE       Process commands from a file"
    echo "  -v, --verbose         Enable verbose output with INFO level logging"
    echo "  -d, --debug           Enable debug mode with detailed logging"
    echo "  -t, --temperature N   Set temperature for response generation"
    echo "  -p, --provider NAME   Set API provider (anthropic or openai)"
    echo "  --git                 Enable Git tracking for changes"
    echo "  --no-git              Disable Git tracking for changes"
    echo "  -h, --help            Show this help message"
    echo
    echo "Examples:"
    echo "  cli.sh 'list all python files'              # Execute a single command"
    echo "  cli.sh -c 'list python files'               # Start a chat session"
    echo "  cli.sh -c 'tell me about those files'       # Continue the chat session"
    echo "  cli.sh -f commands.txt                      # Execute commands from a file"
    echo "  cli.sh -v 'echo verbose mode'               # Run with verbose logging"
}

# Show help if requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

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

# Set Python path for running the CLI
export PYTHONPATH="$(pwd)"

# Check if verbose or debug flag is present
if [[ "$*" == *"-v"* || "$*" == *"--verbose"* ]]; then
    export PYTHONLOGLEVEL=INFO
elif [[ "$*" == *"-d"* || "$*" == *"--debug"* ]]; then
    export PYTHONLOGLEVEL=DEBUG
else
    export PYTHONLOGLEVEL=WARN
fi

# Always use LiteLLM implementation
export VMPILOT_USE_LITELLM=true
export VMPILOT_LITELLM_MODEL="${VMPILOT_LITELLM_MODEL:-gpt-4o}"

python3 src/vmpilot/cli.py "$@"
echo
