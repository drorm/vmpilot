# Project Plugin

The Project Plugin helps users set up and maintain project-specific configuration through the `.vmpilot` directory structure, providing contextual information about the project for each conversation.

## Purpose

This plugin enables VMPilot to:

- Create and manage project-specific configuration files
- Store project context that persists across conversations
- Provide a consistent framework for project documentation
- Streamline the onboarding experience for new projects

## Project Structure

When set up, the project will have the following structure:

```
.vmpilot/
└── prompts/
    └── project.md
```

The `project.md` file contains essential information about the project that's included in the system prompt for each conversation, helping VMPilot understand the project context.

## Setup Process

When a user starts a chat in a project without the `.vmpilot` directory structure, VMPilot will:

1. Detect the missing project structure
2. Present the user with options:
   - **Option A (Recommended)**: Create standard project files from a template
   - **Option B**: Skip project setup and remember this preference

### Option A: Standard Setup

This option creates the `.vmpilot/prompts` directory and populates it with a template `project.md` file that users can customize to describe their project.

The standard setup:

- Creates the necessary directory structure
- Adds a template project description file
- Maintains Git compatibility by respecting existing .gitignore settings

### Option B: Skip Setup

If users prefer not to create the `.vmpilot` directory structure, they can choose to skip setup. VMPilot will:

- Remember this preference for future sessions
- Not prompt again about creating project files
- Continue to function without project-specific context

## Customizing Project Description

After setup, users can either:

1. **Manual Editing**: Edit the `project.md` file directly with their preferred text editor
2. **VMPilot-Assisted Analysis**: Ask VMPilot to analyze the project and suggest a customized description

The `project.md` file should include:

- Project name and description
- Directory structure overview
- Setup and installation instructions
- Development guidelines
- Testing and deployment processes
- Additional resources

## Benefits

Using the Project Plugin provides several advantages:

- **Consistent Context**: VMPilot understands your project better with each interaction
- **Reduced Repetition**: No need to explain project structure repeatedly
- **Improved Recommendations**: More accurate suggestions based on project-specific knowledge
- **Documentation Framework**: Built-in structure for maintaining project documentation

## Usage

To get started with the Project Plugin:

1. Begin a new chat in your project directory
2. VMPilot will detect if the project structure exists
3. If not, choose between standard setup or skipping
4. After setup, customize your `project.md` file to better describe your project

To update your project description at any time, simply edit the `.vmpilot/prompts/project.md` file.
