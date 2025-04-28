# Code Search Tool

The Code Search Tool enables you to search your codebase using natural language queries, helping you find relevant code, understand functionality, and explore project structure.

## Overview

The Code Search Tool is a powerful feature that allows you to:

- Find relevant code using natural language queries
- Understand how specific features are implemented
- Locate functions, classes, or modules related to certain functionality
- Explore error handling, authentication, database connections, and more
- Get explanations of code patterns and implementation details

## Using the Search Tool

### Basic Usage

```yaml
search_code:
  query: "How does user authentication work in this project?"
```

### Advanced Usage

```yaml
search_code:
  query: "Find all functions that handle file uploads"
  project_root: "/path/to/project"
  output_format: "markdown"
  verbose: true
  model: "gemini-1.5-pro"
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | The natural language query to search for in the codebase |
| `project_root` | string | No | Current directory | Root directory of the project to search |
| `config_path` | string | No | Default config | Path to a custom search configuration file |
| `output_format` | string | No | "markdown" | Output format - "markdown", "json", or "text" |
| `verbose` | boolean | No | false | Enable verbose logging |
| `model` | string | No | Config default | LLM model to use for search |

## Examples

### Finding Authentication Logic

**Input:**
```yaml
search_code:
  query: "How is user authentication implemented?"
```

**Output:**
```markdown
## Summary
User authentication uses JWT tokens with a custom middleware that validates tokens against the database.

## Relevant Files
- src/auth/middleware.py
- src/auth/tokens.py
- src/models/user.py

## Key Snippets
```python
# From src/auth/middleware.py
def authenticate_user(token):
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        return User.get_by_id(user_id)
    except jwt.InvalidTokenError:
        return None
```
```

### Finding Error Handling Code

**Input:**
```yaml
search_code:
  query: "How does error handling work in the API routes?"
```

**Output:**
```markdown
## Summary
API error handling uses a global exception middleware that catches all exceptions and formats them as consistent JSON responses with appropriate HTTP status codes.

## Relevant Files
- src/api/errors.py
- src/api/middleware.py
- src/api/routes/base.py

## Key Snippets
```python
# From src/api/errors.py
class APIErrorHandler:
    def __init__(self, app):
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail, "code": exc.status_code},
            )
            
        @app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "code": 500},
            )
```
```

## Configuration

The search tool uses a YAML configuration file to control various aspects of the search process. The default configuration is located at `~/vmpilot/src/codesearch/searchconfig.yaml`.

You can customize:

- File inclusion/exclusion patterns
- Token limits
- Language model selection
- Output formatting preferences

Example configuration:

```yaml
# File patterns
include:
  - src/**/*.py
  - scripts/**/*.sh
  - config/**/*.yaml

exclude:
  - tests/**
  - node_modules/**
  - build/**

# Size limits
limits:
  max_file_size_kb: 500
  max_total_context_tokens: 900000

# LLM settings
llm:
  provider: "google"  # or "openai"
  model: "gemini-1.5-pro"
  temperature: 0.1

# Output settings
output:
  default_format: "markdown"
  max_results: 5
```

## Using Custom Configuration

You can specify a custom configuration file:

```yaml
search_code:
  query: "Find database connection code"
  config_path: "/path/to/custom-config.yaml"
```

## Tips for Effective Code Search

1. **Be specific in your queries**
   - "How is user data validated before saving to the database?" is better than "How does validation work?"

2. **Use natural language**
   - The search tool understands natural questions, so you can ask as you would a human

3. **Specify code concepts**
   - Mention patterns, architecture concepts, or specific technologies in your query

4. **Refine iteratively**
   - If your first search doesn't yield what you need, try a more specific or different query

5. **Limit scope when needed**
   - For large codebases, focus on specific directories by setting the project_root parameter

## Limitations

- The search tool works best with codebases that fit within the LLM's context window
- Very large files may be truncated or excluded
- The tool may occasionally misinterpret complex code patterns
- Search effectiveness depends on the quality and specificity of your query