# VMPilot Prompting System

## Overview
Whenever you start a conversation with an LLM, it has no context or memory of previous interactions. You need to provide context and direction. 
VMPilot uses a multi-level prompting system to ensure the LLM has the necessary context to assist effectively.

## Core Concepts

### 1. Project Context
Using OpenWebUI workspaces, we provide:

- Project root directory location
- Project structure and overview
- Technology stack information
- Development guidelines

### 2. Task Context
Through Github issues integration:

- Current task details and requirements
- Related discussions and context
- Project milestones and labels

## Working with OpenWebUI Workspaces

Workspaces in VMPilot help organize different aspects of your development:

- Project-specific workspaces (e.g., OpenAI VMPilot, Claude VMPilot)
- Development focus areas (Frontend, Backend)
- Personal workspaces

### Essential Workspace Components
When setting up a workspace prompt, include:
- Project root directory (crucial for file operations)
- Technology stack details
- Project description and structure
- Development guidelines

### Setting Up a Workspace
1. Click on "Workspace"
2. Click the "+" button to create a new workspace
3. Enter a name and configure settings
4. Add your project prompt
5. Click "Save"

## Using Github Issues for Context
The Github issues plugin provides task-specific context to the LLM. Simply ask to view an issue:
```bash
Look at github issue <number>
```

## Examples

### Sample Project Prompt
The following is the actual VMPilot project prompt:

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
