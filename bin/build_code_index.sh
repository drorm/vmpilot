#!/bin/bash
# Build the code index for VMPilot

set -e

export ANONYMIZED_TELEMETRY=False
# Default values
SOURCE_DIR="$(pwd)"
VECTOR_STORE_DIR="$HOME/.vmpilot/code_index"
EMBEDDING_MODEL="text-embedding-3-small"

# Help message
function show_help {
    echo "Usage: $0 [options]"
    echo "Build a code index for VMPilot's hybrid RAG system"
    echo ""
    echo "Options:"
    echo "  -s, --source DIR      Source directory to index (default: current directory)"
    echo "  -o, --output DIR      Output directory for vector store (default: ~/.vmpilot/code_index)"
    echo "  -e, --embeddings MODEL Embedding model to use (default: text-embedding-3-small)"
    echo "  -l, --languages LANGS Space-separated list of languages (default: python)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --source ~/myproject --languages python javascript"
}

# Parse arguments
POSITIONAL_ARGS=()
LANGUAGES=("python")

while [[ $# -gt 0 ]]; do
  case $1 in
    -s|--source)
      SOURCE_DIR="$2"
      shift 2
      ;;
    -o|--output)
      VECTOR_STORE_DIR="$2"
      shift 2
      ;;
    -e|--embeddings)
      EMBEDDING_MODEL="$2"
      shift 2
      ;;
    -l|--languages)
      # Consume all arguments until the next option
      LANGUAGES=()
      while [[ $# -gt 1 && ! "$2" =~ ^- ]]; do
        LANGUAGES+=("$2")
        shift
      done
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    -*|--*)
      echo "Unknown option $1"
      show_help
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

# Convert languages array to space-separated string
LANGUAGES_STR=$(IFS=" "; echo "${LANGUAGES[*]}")

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory $SOURCE_DIR does not exist"
    exit 1
fi

# Print settings
echo "Building code index with the following settings:"
echo "Source directory: $SOURCE_DIR"
echo "Vector store directory: $VECTOR_STORE_DIR"
echo "Embedding model: $EMBEDDING_MODEL"
echo "Languages: $LANGUAGES_STR"
echo ""

# Run the direct Python script
$(dirname $0)/code_index.py "$SOURCE_DIR" \
    --vector-store-dir "$VECTOR_STORE_DIR" \
    --embedding-model "$EMBEDDING_MODEL" \
    --languages $LANGUAGES_STR

echo ""
echo "Index built successfully!"
echo "You can now use the code_retrieval tool in VMPilot."
