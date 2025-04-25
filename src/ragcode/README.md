# RAG-based Code Retrieval System

This module provides structure-aware code indexing and hybrid retrieval capabilities for VMPilot.

## Dependencies

The following packages are required:

```
llama-index>=0.10.7
llama-index-core>=0.10.7
llama-index-embeddings-openai>=0.1.5
tree-sitter>=0.20.1
```

Optional dependencies for better performance:

```
llama-index-vector-stores-chroma>=0.1.1
chromadb>=0.4.18
```

## Installation

The core dependencies should already be installed with VMPilot. If you want to use the ChromaVectorStore for better persistence and performance, install:

```bash
pip install llama-index-vector-stores-chroma chromadb
```

## Usage

1. Make sure you have the required dependencies installed:

```bash
pip install llama-index llama-index-embeddings-openai tree-sitter
```

2. Build the code index:

```bash
./bin/build_code_index.sh --source ~/myproject
```

3. Use the code_retrieval tool in VMPilot:

```
Find the implementation of the ShellTool class
```

4. If you encounter any issues, try using the Python script directly:

```bash
./bin/code_index.py ~/myproject
```

## Troubleshooting

### Module not found errors

If you encounter any module not found errors, make sure your PYTHONPATH includes the src directory:

```bash
export PYTHONPATH="$PYTHONPATH:/path/to/vmpilot/src"
```

### Import errors with llama_index

The code has been updated to work with the current llama-index package structure. If you encounter import errors, it may be due to a version mismatch. Check your installed versions:

```bash
pip list | grep llama-index
```

### ChromaVectorStore not available

If you want to use ChromaVectorStore for better persistence, install:

```bash
pip install llama-index-vector-stores-chroma chromadb
```

The system will fall back to SimpleVectorStore if ChromaVectorStore is not available, which works but doesn't provide the same level of persistence and performance.
