# GitHub Issue Plugin for VMPilot

A plugin that enables VMPilot to create and manage GitHub issues directly using the GitHub CLI (`gh`).

## Prerequisites

- GitHub CLI (`gh`) installed and configured
- Authenticated with GitHub (`gh auth login`)

## Usage

This plugin uses VMPilot's shell tool to interact directly with the GitHub CLI. Interview the user for the required information.

**Always get confirmation from the user before creating an issue.**
1. Find out what kind of issue the user wants to create.
2. Look at ~/vmpilot/.github/ISSUE_TEMPLATE and figure out the required fields based on the issue type.
3. Discuss with the user to gather the required information.
4. Use the `gh` CLI to create the issue.

### Creating Issues

Example prompt:
```
create a github issue titled \"Add logging feature\" with label \"enhancement\"
```

This will execute:
```bash
gh issue create --title \"Add logging feature\" --label \"enhancement\"
```

### Common Operations

**IMPORTANT**: All GitHub commands must be executed from the project root directory (/home/dror/vmpilot)

- Create issue: `cd /home/dror/vmpilot && gh issue create`
- List issues: `cd /home/dror/vmpilot && gh issue list`
- View issue: `cd /home/dror/vmpilot && gh issue view`
- Close issue: `cd /home/dror/vmpilot && gh issue close`
- Reopen issue: `cd /home/dror/vmpilot && gh issue reopen`
