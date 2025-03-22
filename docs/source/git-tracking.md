# Git Tracking

VMPilot includes built-in Git integration to track and manage changes made by the AI assistant. This feature ensures all modifications to your codebase are properly recorded, making it easier to review, revert, or understand changes.

## Motivation

Git tracking is optional but highly recommended when working with VMPilot. It provides several benefits:

- **Transparency**: Understand what changes the AI assistant made to the codebase
- **Safety**: Ensure changes are tracked and can be reverted if needed
- **Documentation**: VMPilot automatically generates commit messages for each change

## How Git Tracking Works

When enabled, VMPilot's Git tracking:

1. Checks the status of your Git repository at the start of each exchange
2. Stashes or stops if the repository is dirty, has uncommitted changes
3. Tracks changes made during VMPilot exchanges. An exchange is a request you make and the response and actions taken by VMPilot. At the end of each exchange:
3. Automatically commits changes at the end of each exchange with AI-generated commit messages
4. Provides warnings if the repository is in a dirty state before operations

## Configuration

Configure Git tracking in the `[git]` section of your `config.ini` file:

| Setting | Description | Default | Options |
|---------|-------------|---------|---------|
| enabled | Enable or disable Git tracking | true | true/false |
| dirty_repo_action | Action to take when repository has uncommitted changes | stash | stop, stash |
| auto_commit | Automatically commit changes after each exchange | true | true/false |
| commit_message_style | Style of generated commit messages | bullet_points | short, detailed, bullet_points |
| model | LLM model used for commit message generation | claude-3-7-sonnet-latest | (any supported model) |
| provider | LLM provider for commit message generation | anthropic | anthropic, openai |
| temperature | Temperature for commit message generation | 0.7 | 0.0-1.0 |
| commit_prefix | Prefix added to all commit messages | [VMPilot] | (any text) |

### Example Configuration

```ini
[git]
enabled = true
dirty_repo_action = stash
auto_commit = true
commit_message_style = bullet_points
model = claude-3-7-sonnet-latest
provider = anthropic
temperature = 0.7
commit_prefix = [VMPilot]
```

## Best Practices

1. **Clean Repository**: Start with a clean repository before asking VMPilot to make changes
2. **Review Commits**: Always review the commits made by VMPilot to ensure they're appropriate
3. **Branch Strategy**: Consider having VMPilot work in a dedicated branch for larger changes

## Limitations

- VMPilot cannot resolve complex merge conflicts
- The system works best with simple, linear Git histories
- Very large diffs might result in less precise commit messages
