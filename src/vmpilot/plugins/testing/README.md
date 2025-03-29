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

## LLM Testing Assistance

As an LLM, I can help with three primary testing tasks:

### 1. Creating Unit Tests

When asked to create unit tests, I will:

- Analyze the component to identify test cases
- Plan tests for normal operation, edge cases, and error conditions
- Implement tests following project conventions
- Verify tests pass and provide adequate coverage

### 2. Creating End-to-End Tests

When asked to create e2e tests, I will:

- Create shell scripts in the tests/scripts directory
- Ensure scripts use the TEST_DIR environment variable
- Implement proper test validation and error handling
- Follow the e2e testing patterns established in existing scripts

### 3. Improving Code Coverage

When asked to improve code coverage, I will:

- Run the coverage script to identify gaps
- Focus on files below the threshold
- Generate appropriate tests (unit or e2e) targeting uncovered lines
- Verify improvements by re-running coverage analysis

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
