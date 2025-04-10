# Exchange Integration with VMPilot Agent

This document describes how the `Exchange` class from `exchange.py` has been integrated with the VMPilot agent system to provide Git tracking capabilities for LLM-generated changes.

## Overview

The `Exchange` class represents a single user-LLM interaction with Git tracking capabilities. It has been integrated with the `agent.py` file to automatically track and commit changes made by the LLM during each interaction.

## Key Components

1. **Exchange Class**: Manages a single user-LLM interaction, including:
   - Tracking user and assistant messages
   - Git repository status checking
   - Auto-committing changes with descriptive commit messages
   - Conversation state management

2. **Git Tracking**: Uses `GitTracker` from `git_track.py` to:
   - Check repository status before LLM operations
   - Commit changes made by the LLM with auto-generated commit messages
   - Provide a clean interface for Git operations

3. **CLI Integration**: Added command-line options to:
   - Enable/disable Git tracking
   - Configure commit message style

## Implementation Details

### Changes to agent.py

1. Added `Exchange` initialization at the start of `process_messages`
2. Tracked tool calls during LLM interaction
3. Completed the Exchange with assistant's response and collected tool calls
4. Added error handling to ensure Exchange is completed even when errors occur

### Changes to cli.py

1. Added command-line arguments for Git tracking:
   - `--git` / `--no-git`: Enable/disable Git tracking
   - `--git-commit-style`: Configure commit message style
2. Updated main function to pass Git configuration to Pipeline
3. Added GitConfig creation and handling

### Changes to vmpilot.py

1. Added Git tracking configuration to Pipeline class
2. Updated `process_messages` call to include Git parameters
3. Added configuration syncing for Git settings

## Usage

The integration is transparent to users, with Git tracking enabled by default. Users can:

1. Disable Git tracking with `--no-git` flag
2. Configure commit message style with `--git-commit-style` flag
3. See Git-related information in debug logs

## Testing

A test script is provided at `tests/scripts/test_exchange.py` to verify the Exchange integration works correctly.

## Future Enhancements

1. User prompting for handling uncommitted changes
2. More detailed commit message styles
3. UI integration for Git operations
4. Undo/revert mechanisms for LLM-generated changes