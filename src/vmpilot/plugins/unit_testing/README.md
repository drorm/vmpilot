# Unit Testing Plugin for VMPilot

A plugin that helps developers create and maintain comprehensive unit tests for VMPilot components.

## Purpose

This plugin provides guidance for creating effective unit tests following best practices for test-driven development. It assists developers in creating unit tests for new features, ensuring test coverage, and maintaining a consistent testing approach across the project.

## VMPilot Testing Framework

### Testing Structure
- VMPilot uses pytest for unit testing
- Unit tests are located in the `$PROJECTDIR/tests/unit` directory
- Test files are named with the `test_` prefix
- Test functions also use the `test_` prefix
- Related tests are grouped into classes with the `Test` prefix

### Running Tests
```bash
# Run all unit tests
python3 -m pytest ~/vmpilot/tests/unit/

# Run specific test file
python3 -m pytest ~/vmpilot/tests/unit/test_config.py

# Run specific test class or function
python3 -m pytest ~/vmpilot/tests/unit/test_specific.py::TestClass
python3 -m pytest ~/vmpilot/tests/unit/test_specific.py::TestClass::test_function
```

## Unit Testing Workflow

### 1. Analysis Phase
Interview and collaborate with the user to understand the following:

- Identify the component or function to be tested
- Understand its inputs, outputs, and behavior
- Determine edge cases and potential failure points
- Review existing tests for similar components

### 2. Planning Phase
- Define test cases covering normal operation
- Plan tests for edge cases and error conditions
- Identify dependencies that need to be mocked
- Determine appropriate assertions

### 3. Implementation Phase

Before moving on to the implementation phase, present the test plan to the user for review and approval.

- Create test file with appropriate name
- Implement test functions or classes
- Use fixtures for test setup and teardown
- Mock external dependencies
- Write clear assertions
- Add docstrings explaining test purpose

### 4. Verification Phase
- Run tests to verify they pass
- Check code coverage
- Refine tests as needed
- Document any discovered issues

## Testing Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fixtures for setup and teardown
- Mock external dependencies
- Avoid test interdependence

### 2. Test Coverage
- Test normal operation paths
- Test edge cases and boundary conditions
- Test error handling paths
- Test performance constraints when relevant

### 3. Test Readability
- Use descriptive test names
- Add clear docstrings
- Follow consistent naming patterns
- Structure tests logically

### 4. Test Maintenance
- Keep tests simple and focused
- Update tests when code changes
- Remove obsolete tests
- Refactor tests when needed

## Test Templates

### Class-based Test Template
```python
import pytest
from unittest.mock import Mock, patch
from vmpilot.module import Class

class TestClass:
    """Tests for the Class in module."""
    
    @pytest.fixture
    def instance(self):
        """Create a test instance of Class."""
        return Class(param1="test", param2=123)
    
    def test_method_normal_case(self, instance):
        """Test that method works with normal inputs."""
        result = instance.method("normal input")
        assert result == "expected output"
    
    def test_method_edge_case(self, instance):
        """Test method behavior with edge case input."""
        result = instance.method("")  # Empty string edge case
        assert result == "default output"
    
    def test_method_error_case(self, instance):
        """Test method raises appropriate exception for invalid input."""
        with pytest.raises(ValueError):
            instance.method(None)  # Should raise ValueError
    
    @patch('vmpilot.module.dependency')
    def test_method_with_mock(self, mock_dependency, instance):
        """Test method with mocked dependency."""
        mock_dependency.return_value = "mocked result"
        result = instance.method_with_dependency("input")
        assert result == "processed mocked result"
        mock_dependency.assert_called_once_with("input")
```

### Function-based Test Template
```python
import pytest
from unittest.mock import Mock, patch
from vmpilot.module import function

def test_function_normal_case():
    """Test that function works with normal inputs."""
    result = function("normal input", option=True)
    assert result == "expected output"

def test_function_edge_case():
    """Test function behavior with edge case input."""
    result = function("", option=True)  # Empty string edge case
    assert result == "default output"

def test_function_error_case():
    """Test function raises appropriate exception for invalid input."""
    with pytest.raises(ValueError):
        function(None)  # Should raise ValueError

@patch('vmpilot.module.dependency')
def test_function_with_mock(mock_dependency):
    """Test function with mocked dependency."""
    mock_dependency.return_value = "mocked result"
    result = function("input", option=False)
    assert result == "processed mocked result"
    mock_dependency.assert_called_once_with("input", option=False)
```
