# Using Open WebUI with VMPilot

Open WebUI provides a rich, intuitive interface for interacting with VMPilot. This guide covers how to use the interface effectively after you've completed the [installation process](installation.md).

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

Workspaces allow you to organize different projects or contexts:

- **Creating a Workspace**: Click the "+" icon in the sidebar to create a new workspace
- **Configuring a Workspace**: Set workspace-specific settings, model preferences, and descriptions
- **Switching Workspaces**: Click on a workspace name or search for it in the drop-down on the top right corner

### Chat Features

- **Code Highlighting**: Code blocks are automatically highlighted for readability
- **History Navigation**: Browse previous conversations in the sidebar
- **Response Streaming**: See responses as they're generated. We don't stream the content of each message, but display the message, tool actions, and code blocks as they are generated.

## Advanced Configuration Options

Open WebUI offers tons of features and settings to enhance your experience.
Check these are at the [Open WebUI documentation site](https://docs.openwebui.com/).
