# User Guide

## Introduction
VMpilot is a powerful tool that enables collaboration with Large Language Models (LLMs) in a virtual machine environment. While primarily designed for software development tasks, it can be utilized for any operation that benefits from LLM assistance in a VM context.

## Basic Usage
VMPilot comes with three core tools out of the box:
1. **Shell Tool**: Executes shell commands and scripts
2. **File Editing Tool**: Modifies existing files
3. **File Creation Tool**: Creates new files with specified content

### Security Note
> [!CAUTION]
> VMPilot operates with your user permissions. The LLM can execute any command available to your user account, including:
> - Reading and writing files
> - Installing packages
> - Running system commands
>
> Always ensure you only grant access to directories and permissions you trust the LLM to handle.

## Typical operation

1. Start a new conversation in the OpenWebUI interface
2. Describe the task you want the LLM to perform.
3. The LLM performs the task and provides the output of any commands it runs.
4. Rinse and repeat.

Example:
````
user: create a hello world example in /tmp
claude-VMPilot:
I'll help you create a simple "Hello, World!" program. Since the request is to create a file but doesn't specify the exact filename, I'll create a Python file named hello.py in the /tmp directory.I've created a simple Python "Hello, World!" program in /tmp/hello.py. Let's verify the file was created and check its contents:
$ cat /tmp/hello.py
'''python
#!/usr/bin/env python3

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```

Let's make the script executable and run it to make sure it works:
$ chmod +x /tmp/hello.py && /tmp/hello.py
'''bash
Hello, World!
```

The program has been created successfully and works as expected! The script:

1. Is located at /tmp/hello.py
1. Has proper Python shebang line
1. Uses a main() function with the standard name  check
1. Successfully prints "Hello, World!" when executed
````

### Notes
- The LLM tends to be a bit verbose and has a bias towards action. It will, as is often the case with LLMs, try its best to answer your question, or perform the task you've asked it to do, rather than ask for clarification. You can change that by asking it to just discuss the task or ask for clarification.

- It can perform several operation to accomplish a task. In our case, it created the script, and ran it to verify that it works.

- Outputs are fenced in the appropriate language for easy reading.

- The LLM will often provide additional information about the task it performed, such as the location of the file it created, the contents of the file, and the output of any commands it ran.

# Choosing the provider

We support multiple providers such as OpenAI and Anthropic. You can choose the provider you want to use in the OpenWebUI interface on the top left. This is quite similar to how you would choose a model in OpenAI's interface. We recommend however that you use Workspaces since they allow you to both choose the model and prompt you want to use.

# Additional Features

## Plugins
VMPilot supports various plugins to extend its functionality. See the [Plugins](plugins.md) documentation for details about available plugins and how to use them.

Some key plugins include:

- [GitHub Issues](github_issues.md) - Manage GitHub issues directly from VMPilot
- Code Map - Generate code documentation automatically. This is a work in progress.

## Tips and Best Practices
For tips on getting the most out of VMPilot, including workspace management, prompt engineering, and general best practices, see our [Tips](tips.md) guide.
