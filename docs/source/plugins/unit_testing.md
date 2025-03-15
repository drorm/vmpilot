# Unit Testing Plugin

## Overview

The Unit Testing Plugin assists developers in creating comprehensive unit tests for VMPilot components. It provides guidance, templates, and best practices for implementing effective tests using pytest.

## Key Features

- **Structured Testing Workflow**: Guides you through analysis, planning, implementation, and verification phases
- **Best Practices**: Provides recommendations for test isolation, coverage, readability, and maintenance
- **Test Templates**: Offers ready-to-use templates for both class-based and function-based tests
- **CLI Testing**: Includes specific guidance for testing command-line interfaces

## How to Use the Plugin

When you need to create unit tests for a new feature or component:

1. Ask VMPilot about unit testing best practices
2. Request guidance on testing specific components
3. Ask for test templates that match your needs
4. Get assistance with implementing tests for edge cases

## Example Usage

Here's an example of how to use the Unit Testing Plugin to create tests for a new feature:

```
I've implemented a new feature in the CLI that allows filtering output. 
Can you help me create unit tests for it?
```

VMPilot will guide you through:

1. Analyzing what aspects of the feature need testing
2. Planning test cases for normal operation and edge cases
3. Implementing tests with appropriate fixtures and mocks
4. Verifying that the tests provide adequate coverage

## Test Structure

VMPilot unit tests follow these conventions:

- Test files are named with `test_` prefix
- Test functions also use the `test_` prefix
- Related tests are grouped into classes with `Test` prefix
- Tests use pytest fixtures for setup and teardown
- External dependencies are mocked

## Running Tests

You can run the tests using pytest:

```bash
# Run all unit tests
python3 -m pytest ~/vmpilot/tests/unit/

# Run specific test file
python3 -m pytest ~/vmpilot/tests/unit/test_config.py

# Run specific test class or function
python3 -m pytest ~/vmpilot/tests/unit/test_specific.py::TestClass
python3 -m pytest ~/vmpilot/tests/unit/test_specific.py::TestClass::test_function
```

## CLI Testing Example

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

This test verifies that the main function correctly initializes the Pipeline, passes the command, and processes the response.

## Benefits of Using the Plugin

- **Consistency**: Ensures all tests follow the same structure and patterns
- **Completeness**: Helps identify all necessary test cases
- **Efficiency**: Reduces time spent figuring out how to test components
- **Quality**: Improves overall code quality through comprehensive testing