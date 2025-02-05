# Goal
Create a concise Markdown documentation file for each source file in this project, placing them under `$ROOTDIR/.vmpilot/codemap` in a directory structure that mirrors the original. For instance, if the source file is `src/module1/file1.ts`, the documentation should be created at `.vmpilot/codemap/src/module1/file1.md`.

# *Documentation Template
For each file, use this format shown in ./template.md.

# Guidelines
1. **Brevity**: Summaries should not restate the entire source code. Aim to be succinct but informative.  
2. **Focus**: Highlight the purpose, imports, major classes, functions, and any internal references.  
3. **Directory Structure**: Preserve the original directory structure within `.vmpilot/codemap`.  
4. **Output**: Each documentation file must be a valid Markdown file (suffixed `.md`), containing only one file’s documentation.

# Task
- Traverse the codebase.
- For each relevant source file, generate the Markdown documentation according to the template.
- Save the resulting `.md` files in `.vmpilot/codemap/<mirror-of-path>`.

# Example
If you see a file named `src/controllers/userController.ts`, you would produce:
```
.vmpilot/codemap/src/controllers/userController.md
```
containing the template with a short summary, dependencies, classes, etc.
