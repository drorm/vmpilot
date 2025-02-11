# User guide

# Introduction
VMpilot is a tool that allows you to collaborate with an LLM primarily for software development, but can be used for any tasks that benefits from an LLM operating in a virtual machine.

# Basic usage
Out of the box, VMPilot has several tools
- A shell tool where it can run shell commands
- A file editing tool where it can edit files
- A file creation tool where it can create files

Since it can run a shell command, it can run any command that you can run in a shell. This includes running scripts, installing packages, and running any other command that you can run in a shell.
> [!CAUTION]
Only give the llm access to files and permissions that you are comfortable with. The llm can run any command that you can run in a shell as the logged in user, so it can potentially do anything that you can do in a shell.

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

# Choosing the provider and model

We support multiple providers such as OpenAI and Anthropic. You can choose the provider and model you want to use in the OpenWebUI interface on the top left. This is quite similar to how you would choose a model in OpenAI's interface. We recommend however that you use Workspaces since they allow you to both choose the model and prompt you want to use.

# Additional Features

## Plugins
VMPilot supports various plugins to extend its functionality. See the [Plugins](plugins.md) documentation for details about available plugins and how to use them.

Some key plugins include:
- [GitHub Issues](github_issues.md) - Manage GitHub issues directly from VMPilot
- Code Map - Generate code documentation automatically

## Tips and Best Practices
For tips on getting the most out of VMPilot, including workspace management, prompt engineering, and general best practices, see our [Tips](tips.md) guide.
