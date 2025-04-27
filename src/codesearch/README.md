# Code Search Tool

A standalone Python CLI tool for searching code using natural language queries and LLM (Gemini) for understanding and context.

## Overview

This tool enables developers to search their codebase using natural language queries. It collects relevant files, sends them along with the query to the Gemini API, and returns structured search results.

## Installation

No installation is required beyond ensuring you have the necessary dependencies:

```bash
pip install pyyaml google-generativeai
```

## Usage

### Basic Usage

```bash
python search.py --query "How does the authentication system work?"
```

### Command-line Options

- `--query`, `-q`: Search query (required)
- `--project-root`, `-p`: Root directory of the project (default: current directory)
- `--config`, `-c`: Path to configuration file (default: searchconfig.yaml in the same directory)
- `--output-format`, `-o`: Output format - json, text, or markdown (default: markdown)
- `--verbose`, `-v`: Enable verbose output showing files included and token counts

### Examples

Search the current directory with default settings:
```bash
python search.py --query "How is error handling implemented?"
```

Search a specific project with verbose output:
```bash
python search.py --query "Find all database connection functions" --project-root /path/to/project --verbose
```

Use JSON output format:
```bash
python search.py --query "How is the CLI implemented?" --output-format json
```

## Configuration

The tool uses a YAML configuration file (default: `searchconfig.yaml`) with the following sections:

### File Patterns

```yaml
file_patterns:
  include:
    - "*.py"    # Python files
    - "*.js"    # JavaScript files
    # more patterns...
  
  exclude:
    - "**/node_modules/**"   # Node.js modules
    - "**/.git/**"           # Git directories
    # more patterns...
```

### Limits

```yaml
limits:
  max_file_size_kb: 500      # Maximum file size in KB
  max_total_tokens: 8000     # Maximum tokens for API request
  max_files_to_include: 50   # Maximum number of files to include
```

### API Configuration

```yaml
api:
  provider: "gemini"         # LLM provider
  temperature: 0.2           # Temperature for API requests
  top_p: 0.95                # Top-p for API requests
```

### Output Configuration

```yaml
output:
  default_format: "markdown" # Default output format
```

## Verbose Mode

When using the `--verbose` or `-v` flag, the tool provides additional information to stderr:
- Number of files found matching patterns
- List of files included in the search
- Token count before and after truncation
- Progress updates during API calls

This is useful for debugging and understanding how the tool is processing your codebase.

## Environment Variables

- `GEMINI_API_KEY`: Your Gemini API key (required)

## VMPilot Integration

This tool can be used with VMPilot by invoking it through the shell tool:

```python
# Example VMPilot integration
shell_tool.run("python /path/to/codesearch/search.py --query 'How does authentication work?' --project-root /path/to/project")
```

## Troubleshooting

### API Key Issues
If you encounter API key errors, ensure that the `GEMINI_API_KEY` environment variable is set:

```bash
export GEMINI_API_KEY=your_api_key_here
```

### No Results Found
If the tool doesn't find any relevant files, try:
- Adjusting your search query
- Checking the include/exclude patterns in the configuration
- Increasing the max file size or token limits

### Performance Issues
For large codebases, the tool may take some time to scan all files. Consider:
- Using more specific include/exclude patterns
- Reducing the maximum number of files to include