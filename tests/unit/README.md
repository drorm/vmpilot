# VMPilot Unit Tests

## Overview

This directory contains the unit tests for the VMPilot project. These tests are implemented using the pytest framework and focus on testing individual components of the system in isolation.

## Running Unit Tests

Unit tests can be run using pytest:

```bash
# Run all unit tests
python3 -m pytest ~/vmpilot/tests/unit/

# Run specific test file
python3 -m pytest ~/vmpilot/tests/unit/test_config.py

# Run specific test class or function
python3 -m pytest ~/vmpilot/tests/unit/tools/test_shell.py::TestShellTool
python3 -m pytest ~/vmpilot/tests/unit/tools/test_shell.py::TestShellTool::test_basic_command_execution

# Run with verbose output
python3 -m pytest -v ~/vmpilot/tests/unit/

# Run with coverage report
python3 -m pytest --cov=vmpilot ~/vmpilot/tests/unit/
```

## Directory Structure

```
unit/
├── conftest.py                   # Shared pytest fixtures and configuration
├── test_config.py                # Tests for configuration handling
├── test_config_values.py         # Tests for configuration values validation
└── tools/                        # Tests for system operation tools
    ├── __init__.py
    ├── test_create_file.py       # Tests for file creation functionality
    ├── test_edit_file.py         # Tests for file editing functionality
    ├── test_edit_file_extended.py # Extended tests for file editing edge cases
    └── test_shell.py             # Tests for shell command execution
```

## Testing Approach

Our unit testing follows these principles:

1. **Isolation**: Each test focuses on a single component and mocks dependencies.
2. **Determinism**: Tests produce the same result on each run.
3. **Coverage**: We aim to test all code paths and edge cases.
4. **Speed**: Unit tests are designed to run quickly.

## Writing New Unit Tests

When adding new unit tests:

1. Name test files with `test_` prefix.
2. Use descriptive test function names starting with `test_`.
3. Group related tests into classes with `Test` prefix.
4. Use pytest fixtures for test setup and teardown.
5. Mock external dependencies using pytest-mock.
6. Add docstrings to test functions explaining what they test.

Example:

```python
import pytest
from vmpilot.some_module import SomeClass

class TestSomeClass:
    @pytest.fixture
    def some_instance(self):
        return SomeClass()
        
    def test_specific_functionality(self, some_instance):
        """Test that SomeClass performs its function correctly."""
        result = some_instance.some_method()
        assert result == expected_value
```

## Test Fixtures

Common test fixtures are defined in `conftest.py`. These provide shared setup code for multiple tests, reducing duplication and ensuring consistency.

## Integration with Other Tests

These unit tests complement the system-level tests found in the parent directory. While system tests validate end-to-end functionality, these unit tests ensure that individual components work correctly in isolation.
