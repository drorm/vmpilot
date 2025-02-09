# GitHub Issue Workflow

## Issue Interaction Process

1. When a user mentions a GitHub issue number:
   - Immediately change to the project root directory
   - Fetch the issue information using `gh issue view <number>`
   - Display the relevant information to the user

2. For issue creation:
   - Review issue templates in ~/.github/ISSUE_TEMPLATE
   - Gather required information from user
   - Create issue from project root directory

3. For issue updates:
   - Always execute commands from project root
   - Verify changes with user before executing

## Example Commands

```bash
# View an issue
cd /home/dror/vmpilot && gh issue view 2

# Create an issue
cd /home/dror/vmpilot && gh issue create --title "..." --label "..."

# List issues
cd /home/dror/vmpilot && gh issue list
```