# Prompting

## Overview
Whenever you start a conversation with the LLM it has no context, no memory of previous interactions. You need to give it context and direction. 
In VMPilot, we use a multi-level prompting system to provide context and direction to the LLM.

1. Using OpenWebUI workspaces we provide a project prompt that includes the root directory of the project and a brief overview of the project.
2. We specify the github issue we are working on, and using the plugin, the llm has context about the job.


## Prompts and OpenWebUI workspaces

## Using Workspaces

Workspaces are a powerful organizational tool that allow you to group related pipelines and prompts. Here are some example workspace categories we use in VMPilot:

- OpenAI VMPilot
- Claude VMPilot
- Frontend development
- Backend development
- Personal

When setting up a workspace prompt, include:

- The root directory of your project. This is crucial for file operations so that the llm doesn't hunt for files in the wrong place.
- Your technology stack
- A brief project description and file structure overview

### Creating a Workspace
1. Click on "Workspace"
2. Click the "+" button to create a new workspace
3. Enter a name and configure the prompt and settings
4. Click "Save"

# Project prompt

## Sample prompt

This is the VMPilot prompt used to develop the VMPilot project. 

````markdown

# Project Overview: VMPilot
An AI-driven system operations assistant with CLI and API interfaces.

## Location and structure

The base directory is $HOME/vmpilot.  Always **cd to this directory** before looking at the files.

```bash
cd $HOME/vmpilot && ls
```


Ignore directories not listed below.

├── docs
│   └── source -- Documentation source files
│       └── user-guide
├── src
│   └── vmpilot -- Main source code directory
│       ├── caching
│       ├── plugins
│       │   ├── codemap
│       │   └── github_issues
│       └── tools -- Llm Tool implementations
└── tests
    ├── scripts -- Integration test scripts
    ├── sample_files -- file used by tests
    └── unit -- Unit tests
        └── tools


## Architecture
* Supports multiple deployment modes:
  - CLI mode (vmpilot-cli)
  - Pipeline mode (OpenWebUI compatible, port 9099)

## Development Guidelines
* Tools follow standard interface with required methods
* Pipeline integrates with OpenWebUI specification

#### /src/vmpilot/
Main source code directory containing the core implementation.
- **Core Files**:
  - vmpilot.py: Main application entry point. Implements the Pipeline mode.
  - agent.py: Core implementation for the agent
    - Handles LLM setup and configuration
    - Implements message processing pipeline
    - Manages tool integration
  - config.py: Configuration management
  - cli.py: Command-line interface implementation

#### /src/vmpilot/tools/
Tool implementations for various functionalities.
  - CreateFileTool: Create a file
  - EditTool: Edit a file
  - SetupShellTool: shell tool

#### /bin/
Execution scripts:
- cli.sh: CLI launcher
- run.sh: Main execution script for the openwebui pipeline

#### /tests/
Test suite and testing utilities:
- Test harnesses
- Sample files
- Integration tests

## Key Features

1. **LLM Integration**
   - Supports multiple providers (Anthropic, OpenAI)
   - Configurable models and parameters
   - Streaming response capability

2. **Tool System**
   - Extensible tool framework
   - Built-in file and system operations
   - Error handling and result management

3. **Pipeline Architecture**
   - Message processing pipeline
   - Asynchronous operation support
   - State management and checkpointing

4. **Development Tools**
   - Comprehensive testing framework
   - Deployment automation
   - Development utilities

## Testing and Development
- Structured test suite in /tests
- Integration test scripts
- Sample files for testing

## Common Usage Patterns
### CLI Mode
- cli.sh "Show me /home"
- cli "create a hello world example in /tmp/hello.py" 
````

## Github issues as prompts

To provide context about the current task, we use the `github issues` plugin.  Just ask the llm to view the issue, and it will provide the context. 

## Example
When working on the VMPilot docs, I ask:

```markdown
Look at github issue 3, documentation.   

    I added a new section “Prompting”. I’m concerned, however that experienced users will skip it because they know how to prompt. However, this page has some important info about prompting in vmpilot   
```
And the llm responds:
````markdown
I'll help analyze these points. Let me first look at issue 3 and the documentation.
```
$ cd /home/dror/vmpilot && gh issue view 3 
title:  Documentation System Setup with MkDocs and GitHub Pages
state:  OPEN
author: dror-llm
labels: documentation, enhancement
comments:   2
assignees:  drorm
projects:   
milestone:  0.1
number: 3
--
# Documentation System Setup with MkDocs and GitHub Pages
...
(and 64 more lines)
Let me address each of your points: 

    Regarding the "Prompting" section concern: 
            You're right that this is a valid concern. Since VMPilot has specific prompting requirements/features, I suggest renaming it to something more specific like "VMPilot-Specific Prompting" or "VMPilot Prompt System" to differentiate it from general LLM prompting. This makes it clear that even experienced prompt engineers should read it.
````
