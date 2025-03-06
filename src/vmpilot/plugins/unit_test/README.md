# VMPilot Unit Testing Guide

## Overview

This guide provides a streamlined approach to creating effective unit tests for VMPilot components using pytest. It covers the test creation process, standards, and includes practical templates.

## Test Creation Workflow

When creating unit tests, follow this process:

### 1. Code Analysis
- Examine the component to understand its purpose and behavior
- Identify public methods/functions, input parameters, return values
- Note potential edge cases and dependencies that need mocking

### 2. Test Planning
- Determine which methods/functions need testing
- Plan test fixtures and identify mocking needs
- Design test cases for normal operation, edge cases, and error conditions

### 3. Test Implementation
- Create test files following naming convention: `test_<module_name>.py`
- Group related tests in classes named `Test<ClassName>`
- Design test methods named `test_<function_name>_<scenario>`
- Use Arrange-Act-Assert pattern
- Include proper assertions and mock external dependencies

### 4. Test Verification
- Review test coverage and isolation
- Verify test quality and documentation

## Testing Standards

Adhere to these standards:
- **Isolation**: Tests must run independently
- **Naming**: Use descriptive names that indicate what's being tested
- **Documentation**: Include clear docstrings
- **Mocking**: Use unittest.mock or pytest fixtures to isolate from dependencies
- **Assertions**: Use pytest's assertion system with clear failure messages
- **Parameterization**: Use pytest.mark.parametrize for multiple scenarios

## Code Templates

### Class-Based Tests

```python
"""Tests for the [module_name] module."""

import pytest
from unittest.mock import patch, MagicMock
from vmpilot.[module_path] import [ClassName]

class Test[ClassName]:
    """Test suite for the [ClassName] class."""
    
    @pytest.fixture
    def sample_instance(self):
        """Provides a configured instance for testing."""
        return [ClassName]([parameters])
    
    def test_[method_name]_[scenario](self, sample_instance):
        """Test [method_name] under normal conditions."""
        # Arrange - any additional setup
        
        # Act - call the method being tested
        result = sample_instance.[method_name]([parameters])
        
        # Assert - verify the results
        assert result == [expected_value]
        
    def test_[method_name]_[error_scenario](self):
        """Test [method_name] error handling."""
        # Arrange
        instance = [ClassName]([invalid_parameters])
        
        # Act & Assert - verify the error is raised
        with pytest.raises([ExpectedException]):
            instance.[method_name]([parameters])
            
    @patch('vmpilot.[module_path].[dependency]')
    def test_[method_name]_with_mocked_dependency(self, mock_dependency):
        """Test [method_name] with mocked dependencies."""
        # Arrange - configure the mock
        mock_dependency.return_value = [mock_value]
        instance = [ClassName]([parameters])
        
        # Act
        result = instance.[method_name]([parameters])
        
        # Assert
        assert result == [expected_value]
        mock_dependency.assert_called_once_with([expected_parameters])
```

### Function-Based Tests

```python
"""Tests for the [module_name] module functions."""

import pytest
from unittest.mock import patch
from vmpilot.[module_path] import [function_name]

def test_[function_name]_[scenario]():
    """Test [function_name] under normal conditions."""
    # Arrange
    input_data = [value]
    
    # Act
    result = [function_name](input_data)
    
    # Assert
    assert result == [expected_value]

@pytest.mark.parametrize("input_value,expected_result", [
    ([input1], [expected1]),
    ([input2], [expected2]),
    ([input3], [expected3]),
])
def test_[function_name]_multiple_scenarios(input_value, expected_result):
    """Test [function_name] with multiple input scenarios."""
    result = [function_name](input_value)
    assert result == expected_result
```

## Example Implementation

```python
"""Tests for the config module."""

import pytest
from unittest.mock import patch, MagicMock
from vmpilot.config import Config

class TestConfig:
    """Test suite for the Config class."""
    
    @pytest.fixture
    def sample_config(self, tmp_path):
        """Fixture providing a sample configuration."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("api_key: test_key\ndefault_model: gpt-4")
        return Config(config_path=str(config_file))
    
    def test_load_config_valid_file(self, sample_config):
        """Test that a valid configuration file is loaded correctly."""
        assert sample_config.is_loaded
        assert sample_config.get("api_key") == "test_key"
        assert sample_config.get("default_model") == "gpt-4"
        
    def test_load_config_missing_file(self):
        """Test behavior when configuration file is missing."""
        config = Config(config_path="nonexistent.yaml")
        with pytest.raises(FileNotFoundError):
            config.load()
```