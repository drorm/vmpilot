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
cli.sh  `cat request.sh`
```

Remember to enclose your command in quotes to ensure that it is passed as a single argument to the CLI.
In the last example, we used backticks to execute a command and pass its output as an argument to the CLI.

## Command Line Options

The CLI supports several command line options to customize its behavior:

```
usage: cli.py [-h] [-t TEMPERATURE] [-f FILE] [-p {anthropic,openai}] [-d] [-c [CHAT]] [command]

positional arguments:
  command               Command to execute (not required if using -f/--file)

options:
  -h, --help           Show this help message and exit
  -t TEMPERATURE,      Temperature for response generation (default: 0.8)
  --temperature
  -f FILE, --file FILE Input file with commands (one per line)
  -p {anthropic,openai},
  --provider          API provider to use (default: anthropic)
  -d, --debug         Enable debug mode
  -c [CHAT], --chat [CHAT]
                      Enable chat mode to maintain conversation context. Optional: provide a specific chat ID.
```

### Temperature

The temperature parameter controls the randomness in the response generation. Higher values (e.g., 0.8) make the output more creative but potentially less focused, while lower values (e.g., 0.2) make it more deterministic and focused. As a rule you should not provide a temperature value, since these are set by the API provider. For testing we use a value of 0 so that the output is deterministic.

Example:
```bash
cli.sh -t 0.3 "Write a Python function to calculate factorial"
```

### Chat Mode

Chat mode maintains conversation context across multiple commands, allowing for follow-up questions and references to previous interactions.

Examples:
```bash
# Start a chat session
cli.sh -c "List all Python files"

# Continue the same chat session
cli.sh -c "Explain what these files do"

# Specify a custom chat ID
cli.sh -c my_session_123 "Show system information"

# Combine with file input for batch processing with context
cli.sh -f commands.txt -c
```

### File Input Mode

The file input mode allows you to provide a file containing multiple commands, with each command on a separate line. VMPilot will:
1. It creates a unique chat ID for the session, unless you specify one
2. Processes each line in the file as a separate command while maintaining conversation context
3. This simulates a continuous conversation as if you were interacting with VMPilot in chat mode
It's similar to chat mode, but with commands read from a file, making it easier to process multiple tasks in sequence.

Example:
```bash
cli.sh -f commands.txt
```

Where `commands.txt` might contain:
```
List all files in the current directory
Show me the content of the largest file
Explain what it does
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

4. Chat sessions for complex tasks:
```bash
# First command in a chat session
cli.sh -c "Find all log files with errors"

# Follow-up in the same session
cli.sh -c "Summarize the most common errors"

# Another follow-up
cli.sh -c "Create a script to fix these errors"
```

5. Batch processing with file input:
```bash
# Create a file with multiple commands
echo "List all services running" > tasks.txt
echo "Show disk usage" >> tasks.txt
echo "Find large log files" >> tasks.txt

# Process all commands in sequence with context
cli.sh -f tasks.txt -c
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
4. For file input mode, ensure each command is on a separate line
