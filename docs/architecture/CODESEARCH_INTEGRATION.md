# Code Search Integration with VMPilot

This document summarizes the integration of the code search functionality into VMPilot as a dedicated tool.

## Integration Overview

The code search functionality has been integrated into VMPilot in the following ways:

1. **Standalone CLI Tool**: The original code search functionality is available as a standalone CLI tool in `src/codesearch/`.

2. **Python Module**: The code search functionality can be imported and used programmatically via the `search_project_code()` function.

3. **VMPilot SearchTool**: A dedicated `SearchTool` has been created to make the code search functionality available directly within VMPilot.

## Implementation Details

### 1. Standalone CLI Tool (`src/codesearch/`)

- `search.py`: Main CLI tool with command-line argument handling
- `utils.py`: Helper functions for file collection, token estimation, etc.
- `searchconfig.yaml`: Configuration for file patterns, limits, etc.
- `README.md`: Documentation for the standalone tool

### 2. Python Module Interface

Added a new function to `search.py`:

```python
def search_project_code(
    query: str,
    project_root: Optional[str] = None,
    config_path: Optional[str] = None,
    output_format: str = "markdown",
    model: Optional[str] = None,
) -> str:
    # Implementation...
```

This function provides a clean interface for other Python code to use the search functionality.

### 3. VMPilot SearchTool

Created a new VMPilot tool in `src/vmpilot/tools/searchtool.py` that:
- Defines input parameters using Pydantic models
- Handles parameter validation and defaults
- Calls the `search_project_code()` function
- Properly formats and returns results

### 4. Integration Points

- Updated `src/vmpilot/tools/setup_tools.py` to include the SearchTool
- Updated `src/vmpilot/tools/__init__.py` to export the SearchTool
- Added documentation in `docs/source/tools/searchtool.md`
- Added a README with usage examples in `src/vmpilot/tools/README_SEARCH_TOOL.md`
- Added an example script in `examples/search_code_example.py`
- Updated the main VMPilot README to mention the search capability

### 5. Testing

- Added unit tests in `tests/unit/tools/test_searchtool.py`
- Added an integration test script in `tests/scripts/test_search_integration.sh`

## Usage Examples

### Using the SearchTool in VMPilot

```
search_code:
  query: "How does user authentication work in this project?"
  project_root: "/path/to/project"
```

### Using the CLI Tool Directly

```bash
python ~/vmpilot/src/codesearch/search.py --query "How is error handling implemented?" --project-root ~/myproject
```

### Using the Python Module

```python
from codesearch.search import search_project_code

results = search_project_code(
    query="Find database connection code",
    project_root="/path/to/project"
)
```

## Advantages of This Integration

1. **Separation of Concerns**: The core search functionality remains in the standalone module
2. **Multiple Access Methods**: Users can access the functionality through CLI, Python API, or VMPilot
3. **Maintainability**: Changes to the search algorithm only need to be made in one place
4. **Reusability**: The code search tool can be used outside of VMPilot
5. **Improved UX**: VMPilot users get a dedicated tool with proper parameter validation

## Future Enhancements

1. Add caching to improve performance for repeated queries
2. Support for multiple LLM providers beyond Gemini
3. Implement chunking for very large codebases
4. Add more advanced output formatting options
5. Create a web interface for the standalone tool