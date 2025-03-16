# GitHub Issue Plugin for VMPilot

A plugin that enables VMPilot to create and manage GitHub issues directly using the GitHub CLI (`gh`).

## Important: Plugin and Project Directories

This plugin is located at:
```
$PROJECT_DIR/src/vmpilot/plugins/github_issues
```

## Prerequisites

- GitHub CLI (`gh`) installed and configured
- Authenticated with GitHub (`gh auth login`)

## File Navigation Guide

When working with GitHub issues, you'll need to access these key locations:

1. **Plugin Documentation** (this file):
   ```
   $PROJECT_DIR/src/vmpilot/plugins/github_issues/README.md
   ```

2. **Issue Templates**:
   ```
   $PROJECT_DIR/.github/ISSUE_TEMPLATE/bug.yaml
   $PROJECT_DIR/.github/ISSUE_TEMPLATE/feature.yaml
   ```

Always use absolute paths when accessing these files.

## Usage

This plugin uses VMPilot's shell tool to interact directly with the GitHub CLI. Interview the user for the required information.

**Always get confirmation from the user before creating an issue.**
1. Find out what kind of issue the user wants to create.
2. Look at the appropriate issue template based on issue type:
   - Bug reports: `$PROJECT_ROOT/.github/ISSUE_TEMPLATE/bug.yaml`
   - Feature requests: `$PROJECT_ROOT/.github/ISSUE_TEMPLATE/feature.yaml`
3. Discuss with the user to gather the required information.
4. Draft the issue and present it to the user for review.
5. **IMPORTANT**: Always ask for explicit confirmation before creating the issue. Use phrasing like:
   "Here's the draft of your GitHub issue. Would you like me to create this issue now? Please confirm."
6. Only after receiving explicit confirmation, use the `gh` CLI to create the issue.

## Workflow

### Issue Interaction Process

1. When a user mentions a GitHub issue number:
   - Immediately change to the project root directory
   - Fetch the issue information using `cd $PROJECT_ROOT && gh issue view --comments <number>`
   - Display the relevant information to the user

2. For issue creation:
   - Review the appropriate issue template (bug.yaml or feature.yaml)
   - Gather required information from user
   - Create a draft of the issue content
   - Show the complete draft to the user for review
   - Ask explicitly: "Would you like me to create this GitHub issue now? Please confirm."
   - Wait for explicit user confirmation (yes/approve/create/etc.)
   - Only after confirmation, create the issue from project root directory

3. For issue updates:
   - Always execute commands from project root directory
   - Verify changes with user before executing

### Temporary File Handling

When creating GitHub issues that require content from a file:

1. Generate a unique temporary filename using a timestamp and random number:
   ```bash
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   RANDOM_NUM=$((1000 + RANDOM % 9000))
   TEMP_FILE="/tmp/vmpilot_issue_${TIMESTAMP}_${RANDOM_NUM}.md"
   ```

2. Create the file with your content:
   ```bash
   echo "Issue content goes here" > "$TEMP_FILE"
   ```

3. Use the file with gh commands:
   ```bash
   cd $PROJECT_ROOT && gh issue create --body-file "$TEMP_FILE"
   ```

4. Clean up temporary files after issue creation:
   ```bash
   rm "$TEMP_FILE"
   ```

5. **IMPORTANT**: Execute these as separate commands, not as a single command chain.

### Creating Issues

Example prompt:
```
create a github issue titled "Add logging feature" with label "enhancement"
```

This will execute:
```bash
cd $PROJECT_ROOT && gh issue create --title "Add logging feature" --label "enhancement"
```

### Common Operations

**IMPORTANT**: All GitHub commands must be executed from the project root directory ($PROJECT_ROOT)

- Create issue: `cd $PROJECT_ROOT && gh issue create`
- List issues: `cd $PROJECT_ROOT && gh issue list`
- View issue: `cd $PROJECT_ROOT && gh issue view --comments <number>`
- Close issue: `cd $PROJECT_ROOT && gh issue close <number>`
- Reopen issue: `cd $PROJECT_ROOT && gh issue reopen <number>`

## Available Templates

The following issue templates are available:

1. **Bug Report** (`$PROJECT_ROOT/.github/ISSUE_TEMPLATE/bug.yaml`)
   - Use for reporting bugs and unexpected behavior
   - Required fields: environment, expected behavior, actual behavior, bug summary, steps to reproduce
   - Optional fields: relevant files, logs and screenshots, additional information

2. **Feature Request** (`$PROJECT_ROOT/.github/ISSUE_TEMPLATE/feature.yaml`)
   - Use for suggesting new features
   - Required fields: feature description, motivation, additional context
   - Optional fields: relevant files, possible implementation
