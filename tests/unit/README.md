# VMPilot Unit Tests

## Overview

This directory contains the unit tests for the VMPilot project. These tests are implemented using the pytest framework and focus on testing individual components of the system in isolation.

## Running Unit Tests

Unit tests can be run using pytest:

```bash
# Run all unit tests
python -m pytest ~/vmpilot/tests/unit/

# Run specific test file
python -m pytest ~/vmpilot/tests/unit/test_config.py

# Run specific test class or function
python -m pytest ~/vmpilot/tests/unit/tools/test_shell.py::TestShellTool
python -m pytest ~/vmpilot/tests/unit/tools/test_shell.py::TestShellTool::test_basic_command_execution

# Run with verbose output
python -m pytest -v ~/vmpilot/tests/unit/
```

## Running Tests with Coverage

The project includes a coverage configuration that helps identify untested code. The target coverage threshold is 70%.

```bash
# Run all unit tests with coverage report
python -m pytest --cov=src/vmpilot --cov-report=term-missing tests/unit/

# Run coverage for a specific module
python -m pytest --cov=src/vmpilot/tools/edit_tool.py --cov-report=term-missing tests/unit/

# Run coverage and show only uncovered lines
python -m pytest --cov=src/vmpilot --cov-report=term-missing:skip-covered tests/unit/
```

For more detailed guidance on code coverage and test generation, see the [coverage plugin documentation](/src/vmpilot/plugins/coverage/README.md).

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

Most unit tests in this project are generated with the assistance of LLMs. When requesting new unit tests:

1. Provide the module path that needs testing
2. Share any specific functionality or edge cases to focus on
3. Mention the desired coverage target (default is 70%)

The LLM will follow these conventions:

1. Name test files with `test_` prefix
2. Use descriptive test function names starting with `test_`
3. Group related tests into classes with `Test` prefix
4. Use pytest fixtures for test setup and teardown
5. Mock external dependencies using pytest-mock
6. Add docstrings to test functions explaining what they test

Example of a properly structured test:

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

For detailed guidance on test generation with LLMs, refer to the [coverage plugin documentation](/src/vmpilot/plugins/coverage/README.md).

## Test Fixtures

Common test fixtures are defined in `conftest.py`. These provide shared setup code for multiple tests, reducing duplication and ensuring consistency.

## Integration with Other Tests

These unit tests complement the system-level tests found in the parent directory. While system tests validate end-to-end functionality, these unit tests ensure that individual components work correctly in isolation.

## Coverage Configuration

The project uses `.coveragerc` and `pytest.ini` files in the project root to configure test discovery and coverage reporting. Key settings include:

- Coverage threshold: 70%
- Excluded paths: tests, __init__.py files, generated files
- Report formats: terminal, HTML, and XML

To see files that don't meet the coverage threshold, use the coverage plugin's script:

```bash
# From project root
./src/vmpilot/plugins/coverage/run_coverage.sh
```
