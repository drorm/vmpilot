# Using Open WebUI with VMPilot

Open WebUI provides a rich, intuitive interface for interacting with VMPilot. This guide covers how to use the interface effectively after you've completed the [installation process](installation.md) and have familiarized yourself with the [basic concepts](getting-started.md) of VMPilot.

## Accessing Open WebUI

After starting the VMPilot container, you can access the Open WebUI interface at:

```
http://localhost:8080
```

## First-time Setup

When you first access the Open WebUI interface, you'll need to:

1. Create a user account (the first user automatically becomes the admin)
2. Configure your API keys:
   - Click on your username in the bottom left corner
   - Select "Admin Panel"
   - Click on "Settings" in the top menu
   - Navigate to the "Pipelines" tab
   - Enter your API keys for any providers you want to use: OpenAI, Anthropic, Google.
   - Click "Save"

## Available VMPilot Models

When using Open WebUI with VMPilot, you'll see two models in the pipeline list:

- **VMPilot PipelineAnthropic (Claude)**
- **VMPilot PipelineOpenAI (GPT-4o)**
- **VMPilot PipelineGoogle AI**

Claude is currently the preferred model for VMPilot, as it:
- Handles code-related tasks effectively
- Offers good performance with VMPilot's caching system
- Has been more extensively tested with VMPilot

The landscape of AI models is rapidly evolving, so the other models may also be suitable for your needs. 

You can select your preferred model when creating or editing a workspace.

## Working with the Interface

Open WebUI provides several powerful features for working with VMPilot:

### Workspaces

Workspaces are powerful organizational tools that allow you to group related conversations, projects, and settings:

- **Creating a Workspace**: Click the "+" icon in the sidebar to create a new workspace
- **Configuring a Workspace**: Set workspace-specific settings, model preferences, and system prompts
- **Switching Workspaces**: Click on a workspace name or search for it in the drop-down on the top right corner

#### Effective Workspace Setup

For optimal results when setting up a workspace:

1. **Choose descriptive names** that reflect the purpose of the workspace (e.g., "Frontend Development," "Project X Backend")

2. **Configure the system prompt** with:
   - The root directory of your project: `$PROJECT_ROOT=/path/to/your/project`
   - Your technology stack
   - A brief project description
   - Any specific instructions for the LLM

3. **Select the appropriate model** for your needs:
   - Claude is recommended for code-related tasks
   - GPT models may be better for certain creative tasks

4. **Organize workspaces by project or function**:
   - Create separate workspaces for different projects
   - Consider creating dedicated workspaces for specific tasks (documentation, testing, etc.)
   - Use workspaces to isolate different branches of the same project

#### Example Workspace Categories

- Project-specific workspaces (e.g., "Project X - Frontend")
- Model-specific workspaces (e.g., "Project X with Claude")
- Task-specific workspaces (e.g., "Documentation Generation")
- Branch-specific workspaces (e.g., "Feature Y Development")

### Chat Features

- **Code Highlighting**: Code blocks are automatically highlighted for readability
- **History Navigation**: Browse previous conversations in the sidebar
- **Response Streaming**: See responses as they're generated. We don't stream the content of each message, but display the message, tool actions, and code blocks as they are generated.

### Managing Conversations

Effective conversation management helps you get the most out of VMPilot:

#### Conversation Length

Long conversations can reduce effectiveness as they:
- Consume more tokens
- May lead to context confusion
- Can cause the LLM to hit token limits

For best results:
- Keep conversations focused on specific tasks
- Start new sessions for new topics
- Include relevant context when starting fresh

#### Editing Prompts

You can refine your requests by editing your prompts:
- Click the edit icon next to your message to modify it
- This helps clarify your intent without starting over
- Useful for correcting misunderstandings or adding details

#### Stopping Generation

If the LLM gets stuck or goes in the wrong direction:
- Click the "Stop" button to halt generation
- This lets you redirect the conversation more efficiently
- Particularly useful for long-running operations

## Troubleshooting

### Common Issues

#### "Steps Limit Exceeded" Message

If you see: "Sorry, need more steps to process this request. I've done 25 steps in a row. Let me know if you'd like me to continue."

**Solution**:
- Type "continue" to let the agent proceed
- Or break the task into smaller parts

#### LLM Tool Errors

If you see error messages like:
- "Field required [type=missing, input_value={}, input_type=dict]"
- "messages.1.content.1.tool_use.name: String should match pattern..."

**Causes**:
- Large file edits
- Conversation history too large (8000+ tokens)

**Solutions**:
- Type "continue" to retry
- Create new files instead of editing large ones
- Start a fresh conversation
- Break down complex tasks

#### Connection Issues

If you experience connection problems:

**Solutions**:
- Check that both VMPilot and Open WebUI are running
- Verify API keys are correctly configured
- Check network settings if using remote connections

## Advanced Configuration Options

Open WebUI offers many additional features and settings to enhance your experience.
For more detailed information, visit the [Open WebUI documentation site](https://docs.openwebui.com/).

For VMPilot-specific configurations, refer to our [Configuration Guide](configuration.md).
