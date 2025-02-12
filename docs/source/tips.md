# Tips and Best Practices

## Create a Separate API Key for VMPilot

When you first start using VMPilot, it's recommended to create a dedicated API key to manage costs effectively. This allows you to:
- Set a specific budget for VMPilot usage
- Monitor VMPilot-specific API consumption
- Keep your other API usage separate

## Managing Chat Length

As conversations grow longer, the LLM's responses may become less focused and effective. When this happens:
- Start a new chat session
- Reuse or update your original prompt
- Copy relevant context from the previous conversation if needed

## Working with LLMs Effectively

LLMs can be remarkably capable but also occasionally unpredictable. To get the best results:

- Read about prompt engineering. It's a skill that takes time to develop but it's worth it.
- Don't ask the llm to do too much at once. Break down the task into smaller tasks.
- Sometimes, you just need to do the task yourself, at least part of it. 

# Using OpenWebUI

## Using Workspaces

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

## Edit your prompt

When you're working on a prompt, it's often helpful to edit the original or latest prompt to refine your request. This can help you get more accurate and relevant responses from the LLM.

## Stop the LLM

Sometimes the LLM may get stuck or go in the wrong direction. Hit the "Stop" button to reset the LLM and start fresh.


