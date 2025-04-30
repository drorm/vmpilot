# VMPilot Testing Plugin

This plugin provides comprehensive guidance for the VMPilot testing ecosystem, including unit tests, end-to-end tests, and code coverage analysis.

## Testing Types

VMPilot employs multiple testing approaches:

1. **Unit Tests**: Test individual components in isolation using pytest
2. **End-to-End Tests**: Test complete workflows using shell scripts and LLM-based evaluation
3. **Coverage Analysis**: Combines results from both test types to ensure comprehensive testing

## Directory Structure

```
tests/
├── coverage.sh           # Script for running coverage analysis
├── e2e_tests.sh          # Runner for end-to-end tests
├── scripts/              # Individual e2e test scripts
│   ├── ls_files.sh
│   ├── modify_file.sh
│   └── ...
├── sample_files/         # Test data for e2e tests
├── unit/                 # Unit tests
│   ├── conftest.py       # Shared pytest fixtures
│   ├── test_config.py
│   ├── tools/
│   │   ├── test_shell.py
│   │   └── ...
```

## Running Tests

### Unit Tests
```bash
# Run all unit tests
python -m pytest ~/vmpilot/tests/unit/

# Run specific test file/class/function
python -m pytest ~/vmpilot/tests/unit/test_config.py
python -m pytest ~/vmpilot/tests/unit/test_specific.py::TestClass
python -m pytest ~/vmpilot/tests/unit/test_specific.py::TestClass::test_function
```

### End-to-End Tests
```bash
# Run all e2e tests
cd ~/vmpilot/tests
./e2e_tests.sh

# Run specific e2e tests
./e2e_tests.sh scripts/ls_files.sh scripts/modify_file.sh
```

### Coverage Analysis
```bash
# Run full coverage analysis (unit + e2e tests)
./tests/coverage.sh

# Run with custom threshold (default is 70%)
./tests/coverage.sh -f 80
```

## Testing as Part of CI/CD Workflow

Testing is an integral part of the VMPilot development workflow and CI/CD pipeline, not just an optional activity. The following practices should be followed:

### 1. Creating Unit Tests for New Features

Whenever a new feature is developed:

- Tests must be created alongside the feature implementation
- Tests should cover normal operation, edge cases, and error conditions
- Tests must follow project conventions and patterns
- Tests should pass and provide adequate coverage before the feature is considered complete

### 2. Creating End-to-End Tests for New Workflows

For features that introduce new user-facing workflows:

- E2E tests must be created in the tests/scripts directory
- Tests should use the TEST_DIR environment variable for isolation
- Tests must include proper validation and error handling
- Tests should follow established e2e testing patterns

### 3. Coverage Analysis for Quality Control

Before merging any feature:

- Coverage analysis must be run to identify testing gaps
- Any files below the threshold must be addressed
- Additional tests (unit or e2e) should be created for uncovered lines
- Coverage improvements should be verified by re-running analysis

These practices ensure consistent quality and reliability across the codebase and are enforced through the CI/CD pipeline.

## Test Structure and Patterns

### Unit Test Structure

```python
"""Tests for module_name"""

import pytest
from unittest.mock import patch, MagicMock
from src.vmpilot.module import function_to_test

class TestComponent:
    """Tests for the Component class."""
    
    @pytest.fixture
    def instance(self):
        """Create a test instance."""
        return Component(param="test")
    
    def test_normal_operation(self, instance):
        """Test normal operation."""
        result = instance.method("input")
        assert result == "expected"
    
    def test_edge_case(self, instance):
        """Test edge case."""
        result = instance.method("")
        assert result == "default"
    
    def test_error_handling(self, instance):
        """Test error handling."""
        with pytest.raises(ValueError):
            instance.method(None)
    
    @patch("src.vmpilot.dependency")
    def test_with_mock(self, mock_dependency, instance):
        """Test with mocked dependency."""
        mock_dependency.return_value = "mock"
        result = instance.method_with_dependency()
        assert result == "processed mock"
```

### End-to-End Test Structure

```bash
#!/bin/bash
# Test script for [functionality]

# Exit on any error
set -e

# Check if TEST_DIR is set
if [ -z "$TEST_DIR" ]; then
    echo "ERROR: TEST_DIR environment variable not set"
    exit 1
fi

cd "$TEST_DIR"

# Process arguments for provider
PROVIDER="anthropic"
while getopts "p:" opt; do
  case $opt in
    p) PROVIDER="$OPTARG" ;;
  esac
done

# Run the CLI command with temperature 0 for consistent results
echo "Testing [functionality]..."
OUTPUT=$(PROJECT_ROOT/bin/cli.sh -t 0 -p "$PROVIDER" "Command to test functionality")

# Validate the output
if [[ "$OUTPUT" != *"expected result"* ]]; then
    echo "ERROR: Output does not contain expected results"
    echo "Output: $OUTPUT"
    exit 1
fi

echo "Test passed!"
exit 0
```

## Testing Best Practices

### Unit Testing Best Practices
- **Test isolation**: Each test should be independent
- **Comprehensive coverage**: Test normal paths, edge cases, and error handling
- **Clear structure**: Use descriptive names and docstrings
- **Appropriate mocking**: Mock external dependencies
- **Maintainability**: Keep tests simple and focused

### End-to-End Testing Best Practices
- **Complete workflows**: Test entire features from start to finish
- **Environment isolation**: Use the TEST_DIR environment variable
- **Proper cleanup**: Clean up any created files
- **Deterministic results**: Use -t 0 flag for consistent LLM responses
- **Clear validation**: Clearly check for expected outputs
- **Informative errors**: Provide helpful error messages

## Common Patterns

## Adding New Tests

### Adding Unit Tests

1. Create a new test file in the appropriate location:
   - For module `src/vmpilot/tools/example.py`
   - Create `tests/unit/tools/test_example.py`

2. Follow naming conventions:
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test functions: `test_*`

3. Implement tests following the structure shown above

4. Run the tests to verify they pass:
   ```bash
   python -m pytest tests/unit/tools/test_example.py -v
   ```

### Adding End-to-End Tests

1. Create a new test script in `tests/scripts/`:
   ```bash
   touch tests/scripts/test_new_feature.sh
   chmod +x tests/scripts/test_new_feature.sh
   ```

2. Structure the script following the e2e test pattern:
   - Use TEST_DIR environment variable
   - Process provider argument
   - Run CLI commands with -t 0
   - Validate results
   - Return appropriate exit code

3. Run the test to verify it works:
   ```bash
   cd tests
   ./e2e_tests.sh scripts/test_new_feature.sh
   ```

## LLM-based Evaluation

VMPilot uses an innovative approach to testing where the LLM itself validates the correctness of outputs in e2e tests. This approach:

- Allows for semantic understanding of responses
- Tests complex interactions that would be difficult with exact matching
- Maintains reliability through temperature=0 setting
- Provides flexibility in testing natural language outputs

When writing e2e tests, leverage this approach by having the LLM interpret outputs and determine if they meet the expected criteria.

## Integration with Continuous Integration

The testing framework is designed to integrate with CI/CD pipelines:

- Unit tests run quickly and provide immediate feedback
- E2E tests validate complete workflows
- Coverage analysis ensures comprehensive testing
- All tests can be run with a single command for CI environments

The expected workflow is:
1. Run unit tests during development
2. Run e2e tests for feature validation
3. Run coverage analysis to ensure adequate test coverage
4. Address any gaps with additional tests
