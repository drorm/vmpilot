# File: <relative/path/from/project/root>

## Summary
A concise one- or two-sentence description of the file’s overall purpose, taken from docstrings or a short inference by the LLM.

## Imports / Dependencies
- **Internal**: Mention any imports from within the same project (e.g., `import { logger } from '../utils/logger';`)
- **External**: Note third-party packages (e.g., `import React from 'react';` or `import requests`)

## Key Classes
For each significant class:
- Name of the class
- A brief description of its purpose (possibly from docstring)
- An overview of main methods (names and short explanations)

## Key Functions
For each top-level function:
- Name and short description of what it does
- Important parameters and return types (if obvious)

## Internal References
- Note key references to other modules, functions, or classes that this file depends on or interacts with.

Example:
```markdown
### `class UserController`
- **Description**: Handles user interactions and session management.
- **Methods**:
  - `login()` - Authenticates user credentials.
  - `logout()` - Clears active user session.
