# RAG-based Code Retrieval System

This module provides structure-aware code indexing and hybrid retrieval capabilities for VMPilot.

## Dependencies

The following packages are required:

```
llama-index>=0.10.7
llama-index-core>=0.10.7
llama-index-embeddings-openai>=0.1.5
tree-sitter>=0.20.1
llama-index-vector-stores-chroma>=0.1.1
chromadb>=0.4.18
```

## Installation

The core dependencies should already be installed with VMPilot. The system now uses Chroma as the vector store for better persistence and performance:

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

### Import errors with llama_index

The code has been updated to work with the current llama-index package structure. If you encounter import errors, it may be due to a version mismatch. Check your installed versions:

```bash
pip list | grep llama-index
pip list | grep chromadb
```

### Using Chroma Vector Store

The system now uses Chroma for vector storage, which provides:
- Improved persistence of embeddings
- Better performance for larger codebases
- More robust querying capabilities

If you encounter any issues with Chroma, the system includes fallback mechanisms to ensure continued operation.
