# VMPilot Tips

## Getting Started

### API Key Management
For optimal cost control and usage tracking:
1. Create a dedicated API key for VMPilot
2. Set specific budget limits
3. Monitor usage separately from other API applications
4. Regularly review consumption patterns

### Effective Communication

#### Managing Conversations
Long conversations can reduce effectiveness. To maintain quality:

1. Keep conversations focused on specific tasks
2. Start new sessions for new topics
3. Include relevant context when starting fresh

#### Task Management
Break down complex tasks:
- Divide large tasks into smaller, manageable steps
- Verify each step before proceeding
- Combine manual work with LLM assistance when needed

# Track LLM changes with git

To track changes made by the LLM, if possible, use a clean git branch. That way, you can simply do a `git diff` to see the changes made by the LLM.

## Multi-Project Support

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

5. **Improved plugin functionality**:
   Plugins like GitHub Issues will automatically operate in the correct repository context based on the current project directory.

## Multi-Branch Workspace Support

VMPilot allows you to work on multiple branches or features simultaneously through workspace management:

### Setting Up Multiple Workspaces for Parallel Development

1. **Create separate workspaces for different branches**:
   ```
   Workspace 1: claude-proj1
   $PROJECT_ROOT=~/proj1
   
   Workspace 2: claude-proj2
   $PROJECT_ROOT=~/proj2
   ```

2. **Switch between workspaces** using the OpenWebUI workspace dropdown to instantly change context.

3. **Work on different branches simultaneously**:
   - Each workspace maintains its own repository context
   - You can have the same project in different directories to work on different branches
   - Perfect isolation between features/branches

### Example Workflow

1. Create two workspaces in OpenWebUI:
   - `feature-a` with `$PROJECT_ROOT=~/project-feature-a`
   - `feature-b` with `$PROJECT_ROOT=~/project-feature-b`

2. Clone your repository to both directories and check out different branches in each.

3. Work in the `feature-a` workspace on one feature branch, then switch to the `feature-b` workspace to work on another feature branch.

4. Use standard Git operations to keep branches in sync with the remote repository.

This approach provides clean separation between feature work while maintaining context awareness through OpenWebUI's workspace feature and standard Git practices.

# Using OpenWebUI

## Use Workspaces

Workspaces are powerful organizational tools that allow you to group related pipelines and prompts. Here are some example workspace categories:

- My software with OpenAI
- My software with Anthropic
- Frontend development
- Backend development
- Personal

When setting up a workspace prompt, include:

- The root directory of your project (crucial for file operations)
- Your technology stack
- A brief project description and file structure overview

### Creating a Workspace
1. Click on "Workspace"
2. Click the "+" button to create a new workspace
3. Enter a name and configure the prompt and settings
4. Click "Save"

## Steps limit exceeded

Sometimes you'll see the message: "Sorry, need more steps to process this request. I've done 25 steps in a row. Let me know if you'd like me to continue."
The agent has a built in limit on the number of steps that it can take in a row to prevent it from getting stuck in a loop. The number is defined in the config file as recursion_limit. 
When you see this message, you can either:

- Just type "continue" to let the agent continue
- Break down the task into smaller steps

## LLM Issues and Error Handling

The LLM may run into issues when using tools. You'll see errors like:

- "Field required [type=missing, input_value={}, input_type=dict]"
- "messages.1.content.1.tool_use.name: String should match pattern '^[a-zA-Z0-9_-]{1,64}$'"}"
- "messages.5.content.1.tool_use.name: String should have at most 64 characters'}}"

### Why This Happens

This mostly happens when the LLM tries to edit a file with a large amount of content or when the history becomes large: the full request is 8000 tokens or more. To resolve this try:

- Just type "continue". Often the LLM can recover from the error and just keep going
- Ask the llm to create a new file instead of editing a new
- Start a new shorter conversation
- Break down the task into smaller steps

This is an ongoing issue with LLMs and hopefully will get better with time. We're also working on improving the error handling and recovery mechanisms.


## Edit your prompt

When you're working on a prompt, it's often helpful to edit the original or latest prompt to refine your request. This can help you get more accurate and relevant responses from the LLM.

## Stop the LLM

Sometimes the LLM may get stuck or go in the wrong direction. Hit the "Stop" button to reset the LLM and start fresh.

