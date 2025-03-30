# Coding Standards and Practices

This guide outlines the coding standards and practices recommended for VMPilot project, including code quality tools, style guidelines, and development workflows. Notice that these are python oriented, but can be adapted to other languages.

## Code Quality Tools

VMPilot uses several tools to maintain code quality and consistency across the codebase.

### Pre-commit Hooks

Pre-commit hooks are scripts that run automatically before each commit is finalized. They help catch issues early and ensure consistent code quality.

#### Benefits of Pre-commit Hooks

- Catch formatting and style issues before they enter the codebase
- Ensure consistent code style across contributions
- Reduce code review time by addressing common issues automatically
- Prevent commits that would fail CI checks

#### Setting Up Pre-commit Hooks

After cloning the repository, set up the pre-commit hooks by running:

```bash
./sh/setup_hooks.sh
```

This script will:
1. Create the pre-commit hook in your local repository
2. Make the hook executable
3. Configure it to run our linting tools

#### What the Pre-commit Hook Does

When you run `git commit`, the pre-commit hook automatically:

1. Runs **black** to check Python code formatting
2. Runs **isort** to check import sorting
3. Displays the output of these tools in your terminal
4. Aborts the commit if any issues are found

Example output from a successful pre-commit hook run:

```
Pre-commit hook is running!
Running linting checks...
Running black check...
All done! ✨ 🍰 ✨
46 files left unchanged.
Running isort check...
Skipped 1 files
✅ All linting checks passed!
```

### Code Formatting Tools

#### Black

[Black](https://black.readthedocs.io/) is an uncompromising Python code formatter that reformats entire files to conform to a consistent style.

- Line length: 88 characters
- String quotes: Double quotes for multi-line strings, consistent quotes elsewhere
- No manual formatting needed - Black handles it all

#### isort

[isort](https://pycqa.github.io/isort/) sorts imports alphabetically and automatically separates them into sections:
- Standard library imports
- Third-party imports
- Local application imports

### Troubleshooting Pre-commit Hooks

If you encounter issues with the pre-commit hooks:

1. **Hook not running**: Make sure the hook is executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

2. **Path issues**: If the hook can't find the lint.sh script, run the setup script again:
   ```bash
   ./sh/setup_hooks.sh
   ```

3. **Bypassing hooks (use sparingly)**: If you need to commit without running the hooks:
   ```bash
   git commit --no-verify -m "Your message"
   ```
   Note: This should only be used in exceptional circumstances.

4. **Fixing lint errors**: If the hook finds issues, fix them before committing again. You can often fix formatting issues automatically:
   ```bash
   black .
   isort .
   ```
