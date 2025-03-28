# VMPilot Coverage Plugin

## Overview

This plugin provides guidance for improving and maintaining code coverage in the VMPilot project through LLM-assisted test generation. The LLM (that's me!) can analyze code, identify untested areas, and generate appropriate unit tests to improve coverage.

## LLM-Driven Interactive Workflow

IMPORTANT: Only generate tests after the user has reviewed the coverage results and agreed to proceed.

Follow these steps when asked to handle code coverage tasks:

1. **Run coverage analysis and show results**
From the root of the project, run the following commands to generate coverage reports
   ```bash
   python -m pytest --cov=src/vmpilot --cov-report=term-missing tests/unit/
   ```

2. **Ask for your direction**
   "Based on the coverage results above, would you like me to:
   1. Generate tests for all files below the threshold (default: 70%)
   2. Focus on specific files
   3. Adjust the threshold"

3. **Process according to users' response**
   - For all files: I'll prioritize by lowest coverage first
   - For specific files: I'll focus only on mentioned files
   - For threshold adjustment: I'll run with new threshold

4. **For each file:**
   - I'll analyze the file structure
   - Generate appropriate tests
   - Run coverage again to verify improvement
   - Continue until threshold is met

## LLM Test Generation Process

When you ask me to generate tests for a module, I'll:

1. **Analyze Module**
   - Examine the module's structure, imports, and functions
   - Identify dependencies that need to be mocked
   - Note which lines are not covered by existing tests

2. **Generate Test Structure**
   - Create appropriate test file structure with imports and setup
   - Follow pytest conventions and patterns as defined in `tests/unit/README.md`
   - Tests will be placed in a corresponding location:
     - Source file: `src/vmpilot/tools/example.py`
     - Test file: `tests/unit/tools/test_example.py`
   - Follow the naming conventions: test files with `test_` prefix, test classes with `Test` prefix

3. **Write Tests for Uncovered Functions**
   - Prioritize functions with 0% coverage
   - Create tests for normal operation cases
   - Add tests for edge cases and error conditions
   - Ensure all code paths are exercised

4. **Verify Coverage Improvement**
   ```bash
   python -m pytest --cov=src/vmpilot/path/to/file.py --cov-report=term-missing tests/unit/path/to/test_file.py
   ```

5. **Iterate Until Threshold Reached**
   - Identify remaining uncovered lines
   - Generate additional tests targeting those specific areas
   - Repeat until the configured threshold is reached

## Test Generation Template

Use this template when generating tests:

```python
"""
Tests for [module_name]

This file contains unit tests for the functionality in src/vmpilot/[path/to/module.py]
"""

import pytest
from unittest.mock import patch, MagicMock
# Import the module being tested
from src.vmpilot.[path.to.module] import [functions_to_test]

# [Optional] Add fixtures for common setup
@pytest.fixture
def setup_fixture():
    # Setup code
    yield # Test runs here
    # Teardown code

# Test normal operation
def test_function_normal_operation():
    # Arrange - set up test data
    
    # Act - call the function
    
    # Assert - verify results

# Test edge cases and error conditions
def test_function_edge_case():
    # Test specific edge case
    pass

# Mock dependencies
@patch("src.vmpilot.[path.to.dependency]")
def test_function_with_mocked_dependency(mock_dependency):
    # Configure mock
    mock_dependency.return_value = "mocked_result"
    
    # Test with mock
    pass
```

## Mocking Strategies

### External Libraries
```python
@patch("requests.get")
def test_function_with_external_call(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    mock_get.return_value = mock_response
    
    # Test with mock
```

### File Operations
```python
@patch("builtins.open", new_callable=mock_open, read_data="test data")
def test_function_with_file_operations(mock_file):
    # Test with mock file
```

### VMPilot Components
```python
@patch("src.vmpilot.agent.Agent")
def test_function_with_agent_dependency(mock_agent):
    mock_agent_instance = MagicMock()
    mock_agent.return_value = mock_agent_instance
    mock_agent_instance.process_message.return_value = "processed"
    
    # Test with mock agent
```

## Common Test Patterns

### Testing Functions with Multiple Returns
```python
@pytest.mark.parametrize("input_value,expected_result", [
    ("case1", "result1"),
    ("case2", "result2"),
    ("case3", "result3"),
])
def test_function_multiple_cases(input_value, expected_result):
    result = function_to_test(input_value)
    assert result == expected_result
```

### Testing Exceptions
```python
def test_function_raises_exception():
    with pytest.raises(ValueError) as excinfo:
        function_that_raises()
    assert "expected error message" in str(excinfo.value)
```

### Testing Async Functions
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function_to_test()
    assert result == expected_value
```

## Best Practices

- Focus on testing functionality, not implementation details
- Ensure tests are independent and can run in any order
- Test both normal cases and edge cases/error conditions
- Keep tests simple and focused on a single behavior
- Use descriptive test names that explain the scenario being tested
- Mock external dependencies (APIs, file system, databases)
- Mock other VMPilot components when testing a specific module
- Use pytest fixtures for common mocking needs

## Reporting Results

When I've completed the test generation task, I'll:
1. List all files that were improved
2. Show before/after coverage percentages
3. Note any files that still don't meet the threshold
4. Suggest next steps if needed

## How to Request Test Generation

To request test generation, you can use these prompts:

1. "Generate tests for [module_path]"
2. "Improve coverage for [module_path]"
3. "Run coverage analysis and create tests for modules below [threshold]%"

For example:
- "Generate tests for src/vmpilot/tools/edit_tool.py"
- "Improve coverage for all modules below 70% threshold"

## Test Generation Checklist

- [ ] Imports and setup
- [ ] Tests for normal operation
- [ ] Tests for edge cases
- [ ] Mocking of dependencies
- [ ] Assertions for all code paths
- [ ] Verify coverage improvement
