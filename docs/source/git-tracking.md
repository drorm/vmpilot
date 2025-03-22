# Git Tracking

VMPilot includes built-in Git integration to help track and manage changes made by the AI assistant. This feature ensures that all modifications to your codebase are properly recorded, making it easier to review, revert, or understand changes.

## How Git Tracking Works

When enabled, VMPilot's Git tracking:

1. Checks the status of your Git repository at the start of each exchange
2. Tracks changes made during the assistant's operations
3. Automatically commits changes at the end of each exchange with AI-generated commit messages
4. Provides warnings if the repository is in a dirty state before operations

## Core Components

### Exchange Class

The `Exchange` class manages a single conversation exchange between the user and the assistant, handling Git operations at appropriate times:

```python
class Exchange:
    """Represents a single exchange between user and LLM, with Git tracking."""
    
    def __init__(self, chat_id, user_message, git_enabled=True):
        # Initialize exchange properties
        # Check Git repo status
    
    def check_git_status(self):
        """Check if Git repo is clean, warn if not."""
        # Returns True if clean or Git disabled
    
    def complete(self, assistant_message, tool_calls=None):
        """Complete the exchange with assistant response and handle Git commit."""
        # Commit changes and save conversation state
    
    def commit_changes(self):
        """Commit any changes made during this exchange."""
        # Generate commit message and commit changes
```

### GitTracker Class

The `GitTracker` class handles all Git-related operations:

```python
class GitTracker:
    """Track and manage Git changes for LLM operations."""
    
    def __init__(self, repo_path=None):
        # Initialize with repo path
    
    def get_repo_status(self):
        """Check if repo is clean/dirty/not a repo."""
        # Returns GitStatus enum value
    
    def get_diff(self):
        """Get current diff for uncommitted changes."""
        # Returns diff string
    
    def commit_changes(self, message, author="VMPilot <vmpilot@ai>"):
        """Commit changes with given message."""
        # Commits changes with provided message
```

### Commit Message Generation

VMPilot uses a worker LLM to generate meaningful commit messages based on the diff:

```python
async def generate_commit_message(diff, model="gpt-3.5-turbo"):
    """Generate a commit message using a worker LLM."""
    # Uses an LLM to analyze the diff and generate a commit message
```

## Configuration

You can enable or disable Git tracking in your VMPilot configuration:

```yaml
git_tracking:
  enabled: true
  auto_commit: true
  commit_author: "VMPilot <vmpilot@ai>"
```

## Best Practices

1. **Clean Repository**: Try to start with a clean repository before asking VMPilot to make changes
2. **Review Commits**: Always review the commits made by VMPilot to ensure they're appropriate
3. **Branch Strategy**: Consider having VMPilot work in a dedicated branch for larger changes

## Limitations

- VMPilot cannot resolve complex merge conflicts
- The system works best with simple, linear Git histories
- Very large diffs might result in less precise commit messages