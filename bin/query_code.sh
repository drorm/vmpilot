#!/bin/bash
# Wrapper script for querying the code index

set -e

export ANONYMIZED_TELEMETRY=False
# Default values
VECTOR_STORE_DIR="$HOME/.vmpilot/code_index"
EMBEDDING_MODEL="text-embedding-3-small"
TOP_K=3
FILE_PATH=""
LANGUAGE=""

# Help message
function show_help {
    echo "Usage: $(basename $0) [options] \"your query\""
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -f, --file PATH            Limit search to a specific file path"
    echo "  -l, --language LANG        Filter by programming language"
    echo "  -k, --top-k NUMBER         Number of results to show (default: 3)"
    echo "  -v, --vector-store DIR     Vector store directory (default: ~/.vmpilot/code_index)"
    echo "  -e, --embedding-model NAME Embedding model name (default: text-embedding-3-small)"
    echo ""
    echo "Examples:"
    echo "  $(basename $0) \"Find the implementation of the ShellTool class\""
    echo "  $(basename $0) --file tools/shelltool.py \"class ShellTool\""
    echo "  $(basename $0) --language python \"file creation\""
    echo ""
    echo "Enhanced Features:"
    echo "  * Improved code chunking (150 lines per chunk)"
    echo "  * Better metadata extraction for code structure"
    echo "  * Result deduplication to avoid repetitive matches"
    echo "  * Enriched output with structure information"
    echo ""
    echo "If you're not seeing good results, try:"
    echo "  ./bin/rebuild_code_index.sh --source ~/your-project"
    exit 0
}

# Parse command line arguments
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            ;;
        -f|--file)
            FILE_PATH="$2"
            shift
            shift
            ;;
        -l|--language)
            LANGUAGE="$2"
            shift
            shift
            ;;
        -k|--top-k)
            TOP_K="$2"
            shift
            shift
            ;;
        -v|--vector-store)
            VECTOR_STORE_DIR="$2"
            shift
            shift
            ;;
        -e|--embedding-model)
            EMBEDDING_MODEL="$2"
            shift
            shift
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done
set -- "${POSITIONAL[@]}"

# Check if a query was provided
if [ $# -eq 0 ]; then
    echo "Error: No query provided."
    show_help
fi

# Construct the query command
QUERY="$1"
CMD="./bin/query_code_index.py \"$QUERY\" --top-k $TOP_K --vector-store-dir \"$VECTOR_STORE_DIR\" --embedding-model \"$EMBEDDING_MODEL\""

# Add optional arguments if provided
if [ -n "$FILE_PATH" ]; then
    CMD="$CMD --file-path \"$FILE_PATH\""
fi

if [ -n "$LANGUAGE" ]; then
    CMD="$CMD --language \"$LANGUAGE\""
fi

# Execute the command
echo "Querying: $QUERY"
eval $CMD
