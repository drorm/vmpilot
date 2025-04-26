# Code Query Tools

This directory contains scripts for building and querying the code index used by VMPilot's code retrieval system.

## Available Tools

### `build_code_index.sh`
Builds a vector index of your codebase for semantic search.

```bash
./build_code_index.sh --source ~/myproject
```

### `query_code.sh`
Queries the vector index for relevant code snippets.

```bash
./query_code.sh "Find the implementation of the ShellTool class"
```

## Usage Examples

### Basic Usage
```bash
# Build the index
./build_code_index.sh --source ~/myproject

# Query the index
./query_code.sh "How is configuration loaded"

# Hybrid search
./find_code.sh "class ConfigLoader"
```

### Advanced Usage
```bash
# Limit search to a specific file
./query_code.sh --file tools/shelltool.py "class ShellTool"

# Show more results
./query_code.sh --top-k 5 "database connection"
```

## Documentation

For more detailed documentation, see:
- [Code Retrieval Documentation](../docs/source/code_retrieval.md)
- [Issue #69: Code Retrieval with Hybrid RAG](https://github.com/user/vmpilot/issues/69)
