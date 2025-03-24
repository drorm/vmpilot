# Unit Tests for git_track.py

This document provides an overview of the unit tests created for the `git_track.py` module, which implements Git tracking functionality for VMPilot.

## Test Coverage

The test suite covers the following aspects of the Git tracking functionality:

### 1. GitConfig Tests

- **Default Configuration**: Verifies that the default configuration values are set correctly.
- **Custom Configuration**: Tests initialization with custom configuration values.

### 2. Basic Git Operations

- **Repository Status**: Tests for checking if a directory is a Git repository and determining if it's clean or dirty.
- **Diff Handling**: Tests the enhanced diff functionality, including staged and working directory changes.
- **Commit Operations**: Tests for committing changes with custom messages and authors.

### 3. Stash Management

- **Stash Changes**: Tests for stashing uncommitted changes.
- **Pop Stash**: Tests for restoring stashed changes, including specifying stash indices.
- **Stash Status**: Tests for checking if there are stashed changes.

### 4. Undo Operations

- **Undo Last Commit**: Tests for reverting the last commit.
- **Reset to Previous Commit**: Tests for resetting to previous commits with both hard and soft resets.

### 5. Pre-Execution Checks

- **Clean Repository**: Tests pre-execution checks when the repository is clean.
- **Dirty Repository**: Tests pre-execution checks when the repository has uncommitted changes.
- **Not a Repository**: Tests pre-execution checks when not in a Git repository.
- **Disabled Checks**: Tests when pre-execution checks are disabled in the configuration.

### 6. LLM Integration

- **Commit Message Generation**: Tests for generating commit messages using the LLM.
- **Different Message Styles**: Tests for different commit message styles (short, detailed, bullet points).
- **Different Models**: Tests for using different LLM models and providers.
- **Error Handling**: Tests for handling errors in LLM-based commit message generation.

### 7. Auto-Commit Functionality

- **Auto-Commit Success**: Tests for automatically generating a commit message and committing changes.
- **Auto-Commit Disabled**: Tests when auto-commit is disabled in the configuration.
- **Auto-Commit Failure**: Tests for handling failures during auto-commit.

### 8. Error Handling

- **Subprocess Errors**: Tests for handling subprocess execution errors in various Git operations.
- **Edge Cases**: Tests for handling edge cases like empty repositories and no stashed changes.

## Test Structure

The tests are organized into several test classes:

1. **TestGitConfig**: Tests for the GitConfig dataclass.
2. **TestGitTracker**: Core tests for the GitTracker class.
3. **TestCommitMessageStyles**: Tests for different commit message styles.
4. **TestGitTrackerLLMIntegration**: Tests for the integration with the worker_llm module.
5. **TestErrorHandling**: Tests for error handling in GitTracker.
6. **TestInitialization**: Tests for GitTracker initialization.

## Test Implementation Details

- **Mocking**: Extensive use of `unittest.mock` to mock subprocess calls and LLM functionality.
- **Temporary Directories**: Tests use temporary directories to avoid affecting the real file system.
- **Async Handling**: Special handling for asyncio-based LLM integration.
- **Error Simulation**: Simulation of various error conditions to test robust error handling.

## Future Test Improvements

- **Integration Tests**: Add tests that use actual Git repositories instead of mocks.
- **Performance Tests**: Add tests for handling large repositories and diffs.
- **Edge Case Tests**: Add more tests for unusual Git states and edge cases.
