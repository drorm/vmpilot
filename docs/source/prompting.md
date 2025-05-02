# VMPilot Context Management System

## Understanding VMPilot's Approach
Whenever you start a conversation with an LLM, it has no context or memory of previous interactions. You need to provide context and direction.
VMPilot uses a multi-level prompting system to ensure the LLM has the necessary context to assist effectively.

## Context Layers

### 1. Project Context (Workspace Level)
Managed through OpenWebUI workspaces. Lets VMPilot know the root directory of the project.
```bash
$PROJECT_ROOT=/path/to/project
```
The project plugin will create a `.vmpilot` directory in the project root, containing a `project.md` file with essential information about the project.
The contents of the `project.md` file is included in the system prompt for each conversation, helping VMPilot understand the project context.
See the [Project Plugin](plugins/project.md) for more details.
```

### 2. Task Context (Branch Manager)
Leveraged through the [Branch Manager plugin](plugins/branch_manager.md):

When you ask VMPilot to create a new branch based on a GitHub issue, it will create a new branch with a name based on the issue title and number.
When you start a new conversation in the project and branch, VMPilot includes the text and comments for the issue in the system prompt.
This ensures that VMPilot has the **full context** for the task at hand.

## Workspace Management

### Types of Workspaces
Organize your development environment with purpose-specific workspaces:

1. **Provider-Specific**
   ```yaml
   Examples:
   - OpenAI Development
   - Claude Integration
   - Gemini Integration
   - Local Model Testing
   ```

2. **Domain-Focused**
   ```yaml
   Examples:
   - Frontend Development
   - Backend Services
   - Infrastructure Management
   ```

### Workspace Setup Guide

1. **Initial Configuration**
   ```yaml
   Steps:
   1. Navigate to Workspace Settings
   2. Create New (+) or Edit Existing
   3. Configure Base Settings:
      - Name: [descriptive identifier]
      - Model: [preferred LLM]
      - Temperature: [0.0-1.0]
   ```

2. **Context Setup**
   ```yaml
   Required Information:
   - Project Directory: Absolute path
   - Stack Definition: Technologies used
   - Access Permissions: Required paths
   - Development Rules: Team guidelines
   ```

### Using GitHub Integration

Access issue context with simple commands to the llm:
```markdown
# View specific issue
Look at github issue 42

# List recent issues
Show open issues

# Reference in discussion
Regarding issue 42, can we...
```

### Example: VMPilot Development Prompt
Below is the actual prompt used in VMPilot's development:

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
