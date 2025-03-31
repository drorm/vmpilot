# Testing Plugin

## Overview

The Testing Plugin provides comprehensive guidance for the VMPilot testing ecosystem, including unit tests, end-to-end tests, and code coverage analysis. Testing is an integral part of the VMPilot development workflow and CI/CD pipeline, not just an optional activity.

## Testing Types

VMPilot employs multiple testing approaches:

1. **Unit Tests**: Test individual components in isolation using pytest
2. **End-to-End Tests**: Test complete workflows using shell scripts and LLM-based evaluation
3. **Coverage Analysis**: Combines results from both test types to ensure comprehensive testing

## Key Features

- **Comprehensive Testing Framework**: Supports both unit and end-to-end testing approaches
- **CI/CD Integration**: Testing is integrated into the development workflow and enforced in the CI/CD pipeline
- **Coverage Analysis**: Built-in tools to measure and improve test coverage
- **Best Practices**: Recommendations for test isolation, coverage, readability, and maintenance
- **Test Templates**: Ready-to-use templates for both unit and end-to-end tests

## Testing as Part of Development Workflow

Testing is not an optional activity but a required part of the development process:

1. **Feature Development**: Tests must be created alongside any new feature implementation
2. **Pre-Merge Validation**: Coverage analysis must be run before merging code
3. **CI/CD Enforcement**: The CI/CD pipeline validates test coverage thresholds

## Unit Testing

Unit tests focus on testing individual components in isolation:

- Test files are named with `test_` prefix
- Test functions also use the `test_` prefix
- Related tests are grouped into classes with `Test` prefix
- Tests use pytest fixtures for setup and teardown
- External dependencies are mocked

### Running Unit Tests

```bash
# Run all unit tests
python -m pytest ~/vmpilot/tests/unit/

# Run specific test file/class/function
python -m pytest ~/vmpilot/tests/unit/test_config.py
python -m pytest ~/vmpilot/tests/unit/test_specific.py::TestClass
python -m pytest ~/vmpilot/tests/unit/test_specific.py::TestClass::test_function
```

### Running Tests with Coverage

```bash
# Run all unit tests with coverage report
python -m pytest --cov=src/vmpilot --cov-report=term-missing tests/unit/

# Run coverage for a specific module
python -m pytest --cov=src/vmpilot/tools/edit_tool.py --cov-report=term-missing tests/unit/
```

## End-to-End Testing

End-to-end tests validate complete workflows from the user's perspective:

- Tests are implemented as shell scripts in the `tests/scripts/` directory
- Tests use the `TEST_DIR` environment variable for isolation
- Tests run CLI commands with temperature 0 for consistent results
- Tests validate outputs using both exact matching and LLM-based evaluation

### Running End-to-End Tests

```bash
# Run all e2e tests
cd ~/vmpilot/tests
./e2e_tests.sh

# Run specific e2e tests
./e2e_tests.sh scripts/ls_files.sh scripts/modify_file.sh
```

## Coverage Analysis

The project targets a minimum of 70% code coverage. Coverage analysis helps identify untested code:

```bash
# Run full coverage analysis
cd ~/vmpilot
./tests/coverage.sh

# Run with custom threshold (default is 70%)
./tests/coverage.sh -f 80
```

## Unit Test Example

Here's an example of a unit test for the CLI module:

```python
@pytest.mark.asyncio
class TestMainFunction:
    """Tests for the main async function that runs the CLI."""

    @patch("vmpilot.cli.Pipeline")
    async def test_main_basic_execution(self, mock_pipeline_class):
        """Test basic execution of the main function."""
        # Setup mocks
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline

        # Mock the pipe method to return a simple generator
        mock_pipeline.pipe.return_value = [
            {"type": "text", "text": "Response text"}
        ]

        # Call main with basic parameters
        with patch("builtins.print") as mock_print:
            await main(
                command="list files",
                temperature=0.7,
                provider="openai",
                debug=False,
                chat_id=None
            )

        # Verify pipeline was created and configured correctly
        mock_pipeline_class.assert_called_once()
        mock_pipeline.set_provider.assert_called_once_with("openai")

        # Verify output was printed correctly
        mock_print.assert_called_with("Response text", end="\n", flush=True)
```

## End-to-End Test Example

Here's an example of an end-to-end test script:

```bash
#!/bin/bash
# Test script for file listing functionality

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

# Create test files
echo "Hello world" > test1.txt
echo "print('Hello')" > test2.py

# Run the CLI command with temperature 0 for consistent results
echo "Testing file listing..."
OUTPUT=$(~/vmpilot/bin/cli.sh -t 0 -p "$PROVIDER" "List files in this directory")

# Validate the output
if [[ "$OUTPUT" != *"test1.txt"* || "$OUTPUT" != *"test2.py"* ]]; then
    echo "ERROR: Output does not list the expected files"
    echo "Output: $OUTPUT"
    exit 1
fi

echo "Test passed!"
exit 0
```

## Benefits of Testing Integration

- **Comprehensive Quality Assurance**: Combines unit and end-to-end testing approaches
- **CI/CD Integration**: Tests are automatically run as part of the development pipeline
- **Coverage Requirements**: Enforces minimum test coverage thresholds
- **Standardized Process**: Ensures all features have adequate test coverage
- **Continuous Improvement**: Regular coverage analysis identifies testing gaps
