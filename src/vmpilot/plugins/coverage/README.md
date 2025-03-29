# VMPilot Coverage Plugin

## LLM Instructions

As an LLM, when asked to help with code coverage for VMPilot:

1. **Run the coverage script** to get current coverage data:
   ```bash
   ./tests/coverage.sh
   ```
   This script:
   - Combines unit and e2e test coverage
   - Uses a default threshold of 70% (can be adjusted with `-f` flag)
   - Shows coverage for each file and missing lines

2. **Review the results with the user** and ask for their priorities:
   - Which specific files need improved coverage?
   - Should we focus on files below the threshold?
   - Are there specific functions they want tested?

3. **Generate appropriate tests** that:
   - Target the uncovered lines identified in the report
   - Follow the project's pytest conventions
   - Place tests in the correct location (e.g., `tests/unit/tools/test_example.py`)
   - Use appropriate mocking strategies for dependencies

4. **Verify improvements** by running the coverage script again after tests are added

## Test Patterns

When writing tests, follow these patterns:

- Place tests in the corresponding location in the `tests/unit/` directory
- Use `test_` prefix for test files and functions
- Use `Test` prefix for test classes
- Use pytest fixtures for common setup
- Mock external dependencies and other VMPilot components
- Test both normal operation and error cases

## Example Test Structure

```python
"""Tests for module_name"""

import pytest
from unittest.mock import patch, MagicMock
from src.vmpilot.module import function_to_test

def test_function_normal_operation():
    # Test normal operation

@patch("src.vmpilot.dependency")
def test_function_with_dependency(mock_dependency):
    # Test with mocked dependency
```
