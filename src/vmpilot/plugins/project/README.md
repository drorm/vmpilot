# Project Plugin for VMPilot

This plugin handles project setup for VMPilot by creating the necessary `.vmpilot` directory structure and files.

## Project Setup Flow

When a user starts a chat in a project without the `.vmpilot` directory structure, VMPilot will:

1. Detect the missing project structure
2. Present the user with options:
   - **Option A (Recommended)**: Create standard project files from a template using `standard_setup.sh`
   - **Option B**: Skip project setup and remember this preference using `skip_setup.sh`

## Directory Structure

When set up, the project will have the following structure:
```
.vmpilot/
└── prompts/
    └── project.md
```

The `project.md` file contains information about the project that's included in the system prompt for each conversation, helping VMPilot understand the project context.

## Scripts

- **standard_setup.sh**: Creates the `.vmpilot/prompts` directory and copies the template `project.md` file
- **skip_setup.sh**: Creates a flag to skip project setup checks for this project in the future

## Customizing Project Description

After setup, users can either:
1. Edit the `project.md` file manually
2. Ask VMPilot to analyze the project and suggest a customized description

This structure provides a consistent way for VMPilot to understand project context while giving users flexibility in how they describe their projects.
