# Getting Started with VMPilot

## Introduction
VMPilot is a powerful tool that enables collaboration with Large Language Models (LLMs) in a virtual machine environment. While primarily designed for software development tasks, it can be utilized for any operation that benefits from LLM assistance in a VM context.

## Setting Up Your Environment

Before you start using VMPilot, make sure you have:

1. Completed the [installation process](installation.md)
2. Configured your [API keys](installation.md#22-configuring-api-keys)
3. Familiarized yourself with the [Open WebUI interface](using-webui.md)

For optimal cost control and usage tracking:
1. Create a dedicated API key for VMPilot
2. Set specific budget limits
3. Monitor usage separately from other API applications
4. Regularly review consumption patterns

## Basic Usage
VMPilot comes with three core tools out of the box:

1. **Shell Tool**: Executes shell commands and scripts
2. **File Editing Tool**: Modifies existing files
3. **File Creation Tool**: Creates new files with specified content

Obviously, using the shell tool, the LLM can do everything it needs to do. Editing files is hard for LLMS, so the file editing tool provides better structure for that. The file creation tool mostly provides good error reporting and structure for creating files.

## Effective Communication with VMPilot

### Managing Conversations
Long conversations can reduce effectiveness. To maintain quality:

1. Keep conversations focused on specific tasks
2. Start new sessions for new topics
3. Include relevant context when starting fresh

### Task Management
Break down complex tasks:
- Divide large tasks into smaller, manageable steps
- Verify each step before proceeding
- Combine manual work with LLM assistance when needed

### Security Note
> [!CAUTION]
> VMPilot operates with the user permissions. The LLM can execute any command available to the user account, including:
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

### Tracking Changes with Git

To track changes made by the LLM, we recommend using a clean git branch. This approach allows you to:

1. See exactly what the LLM has modified using `git diff`
2. Review changes before committing them
3. Maintain a clean history of your collaboration with the LLM
4. Easily revert changes if needed

Example of a typical VMPilot interaction:
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
- The LLM tends to be a bit verbose and has a bias towards action. It will, as is often the case with LLMs, try its best to answer your question, or perform the task you've asked it to do, rather than ask for clarification. You can change that by asking it to just discuss the task or ask for clarification. You can also, in your prompt, change its behavior.

- It typically performs several operations to accomplish a task. In our case, it created the script, and ran it to verify that it works.

- Outputs are fenced in the appropriate language for easy reading.

- The LLM will often provide additional information about the task it performed, such as the location of the file it created, the contents of the file, and the output of any commands it ran.

- With the multi-project support feature, you no longer need to explicitly tell the LLM where your project is located in each prompt. Configure it once in your workspace system prompt with `$PROJECT_ROOT=/path/to/your/project` and VMPilot will automatically maintain the correct context.

# Choosing the provider

We support Anthropic primarily, but you can also try OpenAI. You choose the provider you want to use in the OpenWebUI interface on the top left. This is quite similar to how you would choose a model in OpenAI's interface. We recommend however that you use Workspaces since they allow you to both choose the model and prompt you want to use.

## Working with Projects

VMPilot is designed to work with projects and git repos. A project is a directory containing all the files and resources for your project, typically a git repository. VMPilot can work with multiple projects simultaneously, allowing you to switch between them easily.

**VMPilot automatically performs a 'cd' to the project directory when starting a chat**, ensuring all file paths, shell commands, and operations are relative to the project directory.

### Project Directory Configuration

There are two ways to specify which project directory VMPilot should use:

1. **Default Project Directory**: Set in `config.ini` using the `default_project` setting under the `[general]` section. This is used when no specific project is identified in a workspace.

2. **Workspace-Specific Project Directory**: Specify the project root in your workspace system prompt using:
   ```
   $PROJECT_ROOT=/path/to/your/project
   ```

### Multi-Project Support

The multi-project support feature simplifies working with multiple codebases:

1. **No need for manual project root specification**:
   Previously, you had to include phrases like "The root directory of this project is '/path/to/project'" in your prompts. Now simply add `$PROJECT_ROOT=/path/to/your/project` to your workspace system prompt once.

2. **Workspace-specific project contexts**:
   - Create separate workspaces for different projects
   - Each workspace maintains its own project context
   - All operations (file editing, shell commands, git) automatically work in the correct directory

3. **Set a default project**:
   Configure `default_project` in your `config.ini` file to provide a fallback when no project is specified.

4. **Seamless project switching**:
   When switching between workspaces, VMPilot automatically changes to the appropriate project directory without any additional commands.

### Multi-Branch Development

VMPilot supports working on multiple branches or features simultaneously through workspace management:

#### Setting Up for Parallel Development

1. **Create separate workspaces for different branches**:
   ```
   Workspace 1: feature-a
   $PROJECT_ROOT=~/project-feature-a

   Workspace 2: feature-b
   $PROJECT_ROOT=~/project-feature-b
   ```

2. **Switch between workspaces** using the OpenWebUI workspace dropdown to instantly change context.

3. **Work on different branches simultaneously**:
   - Each workspace maintains its own repository context
   - You can have the same project in different directories to work on different branches
   - Perfect isolation between features/branches

#### Example Workflow

1. Create two workspaces in OpenWebUI:
   - `feature-a` with `$PROJECT_ROOT=~/project-feature-a`
   - `feature-b` with `$PROJECT_ROOT=~/project-feature-b`

2. Clone your repository to both directories and check out different branches in each.

3. Work in the `feature-a` workspace on one feature branch, then switch to the `feature-b` workspace to work on another feature branch.

4. Use standard Git operations to keep branches in sync with the remote repository.

This approach provides clean separation between feature work while maintaining context awareness through OpenWebUI's workspace feature and standard Git practices.

## Troubleshooting

### Steps Limit Exceeded

If you see the message: "Sorry, need more steps to process this request. I've done 25 steps in a row. Let me know if you'd like me to continue," this means the agent has reached its built-in recursion limit. This limit prevents it from getting stuck in a loop.

When you see this message, you can either:
- Type "continue" to let the agent continue processing
- Break down the task into smaller steps

### LLM Issues and Error Handling

The LLM may sometimes encounter errors when using tools. Common errors include:

- "Field required [type=missing, input_value={}, input_type=dict]"
- "messages.1.content.1.tool_use.name: String should match pattern '^[a-zA-Z0-9_-]{1,64}$'"}"
- "messages.5.content.1.tool_use.name: String should have at most 64 characters'}}"

These errors typically occur when:
- The LLM tries to edit a file with a large amount of content
- The conversation history becomes too large (8000+ tokens)

To resolve these issues:
- Type "continue" to let the LLM recover and continue
- Ask the LLM to create a new file instead of editing an existing one
- Start a new, shorter conversation
- Break down the task into smaller steps

### Stopping the LLM

If the LLM gets stuck or goes in the wrong direction, hit the "Stop" button to reset the LLM and start fresh.

## Additional Features

### Plugins
VMPilot supports various plugins to extend its functionality. See the [Plugins](plugins/overview.md) documentation for details about available plugins and how to use them.

Some key plugins include:

- [GitHub Issues](plugins/github.md) - Manage GitHub issues directly from VMPilot
- [Documentation](plugins/documentation.md) - Create clear, concise, and user-friendly documentation
- [Testing](plugins/testing.md) - Create comprehensive tests for VMPilot components (unit tests, end-to-end tests, coverage analysis)
- Code Map - Generate code documentation automatically. This is a work in progress.

### Next Steps
For more detailed information about using the web interface, see [Using Open WebUI with VMPilot](using-webui.md).
