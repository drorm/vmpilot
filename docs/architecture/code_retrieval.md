# Code Retrieval with Hybrid RAG and Chroma

VMPilot includes a powerful code retrieval system that combines semantic search with structure-aware code chunking. This feature helps you navigate and understand codebases more effectively by finding relevant code snippets based on natural language queries. The system now uses Chroma as the vector store for improved performance and persistence.

## Recent Improvements

We've implemented several improvements to address previous issues with the code retrieval system:

1. **Enhanced Metadata Extraction**
   - Added detection of code structures (classes, functions, methods)
   - Extracted names, relationships, and docstrings
   - Included import statements and inheritance information

2. **Improved Code Chunking**
   - Increased default chunk size from 40 to 150 lines
   - Increased chunk overlap from 15 to 75 lines
   - Created more comprehensive code chunks that include implementations

3. **Result Deduplication**
   - Added content-based deduplication to eliminate duplicate results
   - Preserved the highest scoring match when duplicates are found

4. **Enhanced Result Formatting**
   - Added structure information to search results
   - Included docstring descriptions when available
   - Improved readability with better titles and context

5. **Fixed Directory Structure**
   - Moved the code from `src/ragcode/` to `src/vmpilot/ragcode/`
   - Updated import paths for proper integration

## How It Works

The code retrieval system uses a hybrid Retrieval-Augmented Generation (RAG) approach:

1. **Structure-Aware Chunking**: Source code is split into semantically meaningful chunks (functions, classes, methods) using Tree-sitter, preserving the code's structure.

2. **Vector Embeddings**: These chunks are embedded using OpenAI's `text-embedding-3-small` model (or another configured model) to capture semantic meaning.

3. **Chroma Vector Store**: Embeddings are stored in a Chroma database, providing efficient similarity search and robust persistence.

4. **Hybrid Retrieval**: When you query the system, it uses a combination of:
   - Vector similarity search to find semantically relevant code
   - Re-ranking to prioritize the most useful results
   - Fallback to traditional shell-based tools when needed

## Getting Started

### Building the Code Index

Before using the code retrieval feature, you need to build an index of your codebase:

```bash
# Basic usage (indexes current directory)
./bin/build_code_index.sh

# Index a specific project
./bin/build_code_index.sh --source ~/myproject

# Index multiple languages
./bin/build_code_index.sh --source ~/myproject --languages python javascript
```

The index is stored in `~/.vmpilot/code_index` by default but can be configured with the `--output` option.

### Using Code Retrieval

There are multiple ways to query the code index:

#### 1. Using the Query Script

The `query_code.sh` script provides a simple interface for querying the code index:

```bash
./bin/query_code.sh "Find the implementation of the ShellTool class"
```

Optional parameters:
- `--file <path>`: Limit search to a specific file path
- `--language <lang>`: Filter by programming language
- `--top-k <number>`: Number of results to show (default: 3)

Example:
```bash
./bin/query_code.sh --file tools/shelltool.py "class ShellTool"
```

#### 2. Using the Hybrid Search

For more comprehensive results, you can use the hybrid search tool that combines vector search with grep:

```bash
./bin/find_code.sh "class ShellTool"
```

This tool will:
1. First try the vector-based code retrieval
2. Then fall back to grep-based search
3. Show results from both approaches

Optional parameters:
- `--source <dir>`: Source directory to search (default: ~/vmpilot/src)
- `--language <lang>`: File extension to search (default: python)
- `--top-k <number>`: Number of results to show (default: 3)

#### 3. Using VMPilot's Agent

The code retrieval system is also integrated with VMPilot's agent through the `code_retrieval` tool:

```
Find the implementation of the ShellTool class
```

```
How is configuration loaded in the project?
```

```
Show me code related to GitHub issue handling
```

The tool will return the most relevant code snippets along with their file locations and relevance scores.

## Advanced Usage

### Command-Line Options

The `build_code_index.sh` script supports several options:

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --source` | Source directory to index | Current directory |
| `-o, --output` | Output directory for vector store | `~/.vmpilot/code_index` |
| `-e, --embeddings` | Embedding model to use | `text-embedding-3-small` |
| `-l, --languages` | Languages to index | `python` |
| `-h, --help` | Show help message | |

### Supported Languages

The code chunker supports these languages:

- Python
- JavaScript/TypeScript
- Java
- Go
- Rust
- C/C++

Add support for additional languages by installing the appropriate Tree-sitter grammar.

## Troubleshooting

### Index Not Found

If VMPilot reports that the code index is not found, ensure you've built the index:

```bash
./bin/build_code_index.sh --source <your-project-directory>
```

### Chroma-Related Issues

If you encounter issues related to Chroma:

1. Ensure you have the required dependencies installed:
   ```bash
   pip install llama-index-vector-stores-chroma chromadb
   ```

2. Test your Chroma installation:
   ```bash
   ./bin/test_chroma_integration.sh
   ```

3. If you're migrating from an older version, use the migration script:
   ```bash
   ./bin/migrate_to_chroma.sh --source <your-project-directory>
   ```

### Poor Retrieval Results

If you're getting irrelevant results:

1. Try more specific queries
2. Rebuild the index with a smaller chunk size:
   ```bash
   ./bin/build_code_index.sh --source <dir> --chunk-size 500
   ```
3. Use the hybrid search for more comprehensive results:
   ```bash
   ./bin/find_code.sh "function_name"
   ```
4. Fall back to shell commands for precise searches:
   ```
   grep -r "function_name" --include="*.py" .
   ```
5. Try the enhanced rebuild script:
   ```bash
   ./bin/rebuild_code_index.sh --source ~/your-project
   ```
6. Test the enhanced search:
   ```bash
   ./bin/test_code_search.sh
   ```

### Debugging the Index

To debug issues with the code index, you can use:

```bash
./bin/debug_code_index.py
```

This will show:
- Contents of the vector store directory
- Test queries and their results
- Diagnostic information about the retrieval process

## How It Compares to Shell Tools

While traditional shell tools (`grep`, `find`, etc.) are excellent for exact pattern matching, the code retrieval system offers these advantages:

1. **Semantic understanding**: Find code based on concepts, not just text patterns
2. **Structure awareness**: Results respect function and class boundaries
3. **Relevance ranking**: Most useful results appear first
4. **Natural language queries**: Ask in plain English instead of regex

Shell tools remain available as a fallback for cases where exact pattern matching is preferred.

## Future Work

While we've addressed many immediate issues, there are still opportunities for further improvement:

1. **LLM-based re-ranking**: Implement the placeholder for LLM re-ranking
2. **Call graph integration**: Add understanding of function calls and dependencies
3. **Incremental indexing**: Support updating only changed files
4. **Custom chunking strategies**: Different strategies for different file types

## Testing

To verify the improvements, we recommend:

1. Rebuilding the index with the new settings
2. Running the test script to see the improvements in action
3. Comparing search results before and after the changes
