# Command Line Interface (CLI)

VMPilot provides a powerful command-line interface that allows you to interact with the tool directly from your terminal. 

## Basic Usage

The basic syntax for using the CLI is:

```bash
cli.sh "your command here"
```

For example:
```bash
cli.sh "Show me the contents of /etc/hosts"
cli.sh "Create a new Python script that prints Hello World"
cli.sh  cli.sh  `cat reqeust.sh`
```

Remember to enclose your command in quotes to ensure that it is passed as a single argument to the CLI. 
In the last example, we used backticks to execute a command and pass its output as an argument to the CLI.

## Command Line Options

The CLI supports several command line options to customize its behavior:

```
usage: cli.sh [-h] [-t TEMPERATURE] [-p {anthropic,openai}] [-d] request

positional arguments:
  request               request to the llm

options:
  -h, --help           Show this help message and exit
  -t TEMPERATURE,      Temperature for response generation (default: 0.7)
  --temperature
  -p {anthropic,openai},
  --provider          API provider to use (default: anthropic)
  -d, --debug         Enable debug mode
```

### Temperature

The temperature parameter controls the randomness in the response generation. Higher values (e.g., 0.8) make the output more creative but potentially less focused, while lower values (e.g., 0.2) make it more deterministic and focused. As a rule you should not provide a temperature value, since these are set by the API provider. For testing we use a value of 0 so that the output is deterministic.

Example:
```bash
cli.sh -t 0.3 "Write a Python function to calculate factorial"
```

### Provider Selection

You can choose between different LLM providers:
- anthropic (default)
- openai

Example:
```bash
cli.sh -p openai "Explain how to use the ls command"
```

### Debug Mode

Enable debug mode to see detailed logging information, which can be helpful for troubleshooting:

```bash
cli.sh -d "Show system information"
```

## Examples

Here are some common usage examples:

1. Basic system operations:
```bash
cli.sh "Show me all Python files in the current directory"
cli.sh "Create a new directory called 'test' and add a README file"
```

2. File editing:
```bash
cli.sh "Change the word 'error' to 'warning' in log.txt"
cli.sh "Add a new function to myscript.py"
```

3. Using different providers with custom temperature:
```bash
cli.sh -p openai -t 0.5 "Optimize this Python script for performance"
```

## Error Handling

The CLI will display error messages when:
- The command execution fails
- There are permission issues
- The LLM provider is not properly configured
- Invalid arguments are provided

If you encounter errors, try:
1. Using debug mode (-d) to get more information
2. Checking your API provider configuration
3. Verifying you have the necessary permissions for the requested operation
