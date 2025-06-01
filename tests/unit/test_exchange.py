import time
from datetime import datetime, timedelta

import pytest

from vmpilot import exchange
from vmpilot.exchange import Exchange


# Dummy GitStatus with objects that have a 'name' attribute
class DummyStatus:
    def __init__(self, name):
        self.name = name


# Define DummyGitStatus constants as instances of DummyStatus
class DummyGitStatus:
    DIRTY = DummyStatus("dirty")
    CLEAN = DummyStatus("clean")


# Dummy GitTracker
class DummyGitTracker:
    def __init__(
        self, status=DummyGitStatus.CLEAN, stash_success=True, auto_commit_success=True
    ):
        self._status = status
        self.stash_success = stash_success
        self.auto_commit_success = auto_commit_success
        self.auto_commit_called = False
        self.stash_called = False

    def get_repo_status(self):
        return self._status

    def stash_changes(self, message):
        self.stash_called = True
        return self.stash_success

    def auto_commit_changes(self):
        self.auto_commit_called = True
        if self.auto_commit_success:
            return (True, "Commit successful\nDetails...")
        else:
            return (False, "Commit failed due to error")


# Dummy save function
saved_states = {}


def dummy_save_conversation_state(chat_id, messages, extra):
    saved_states[chat_id] = (messages, extra)


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    # Patch config.git_config and config
    dummy_git_config = type("DummyGitConfig", (), {})()
    dummy_git_config.enabled = True
    dummy_git_config.dirty_repo_action = "stop"
    monkeypatch.setattr(
        exchange, "config", type("DummyConfig", (), {"git_config": dummy_git_config})
    )

    # Patch GitTracker and GitStatus in exchange module
    monkeypatch.setattr(exchange, "GitTracker", lambda: DummyGitTracker())
    monkeypatch.setattr(exchange, "GitStatus", DummyGitStatus)

    # Clear saved_states before each test
    saved_states.clear()


def test_init_with_dict_message():
    chat_id = "chat1"
    user_msg = {"role": "user", "content": "Hello"}
    ex = Exchange(chat_id, user_msg)
    assert ex.user_message["role"] == "user"
    assert ex.user_message["content"] == "Hello"
    assert ex.completed_at is None


def test_init_with_human_message():
    chat_id = "chat2"
    user_msg = {"role": "user", "content": "Hi there"}
    ex = Exchange(chat_id, user_msg)
    assert ex.user_message["content"] == "Hi there"


def test_check_git_status_clean(monkeypatch):
    # Setup: git enabled, repo status is CLEAN
    dummy_tracker = DummyGitTracker(status=DummyGitStatus.CLEAN)
    monkeypatch.setattr(exchange, "GitTracker", lambda: dummy_tracker)
    # Also set dirty_repo_action irrelevant for clean state
    exchange.config.git_config.dirty_repo_action = "stop"

    ex = Exchange("chat_clean", {"content": "Test"})
    # Explicitly test check_git_status
    result = ex.check_git_status()
    assert result is True


def test_check_git_status_dirty_stop(monkeypatch):
    # Setup: git enabled, repo status is DIRTY and action is 'stop'
    dummy_tracker = DummyGitTracker(status=DummyGitStatus.DIRTY)
    monkeypatch.setattr(exchange, "GitTracker", lambda: dummy_tracker)
    exchange.config.git_config.dirty_repo_action = "stop"

    ex = Exchange("chat_dirty_stop", {"content": "Test"})
    result = ex.check_git_status()
    assert result is False


def test_check_git_status_dirty_stash_success(monkeypatch):
    # Setup: git enabled, repo status is DIRTY and action is 'stash', stash successful
    dummy_tracker = DummyGitTracker(status=DummyGitStatus.DIRTY, stash_success=True)
    monkeypatch.setattr(exchange, "GitTracker", lambda: dummy_tracker)
    exchange.config.git_config.dirty_repo_action = "stash"

    callback_called = False

    def dummy_callback(message):
        nonlocal callback_called
        callback_called = True

    ex = Exchange(
        "chat_dirty_stash", {"content": "Test"}, output_callback=dummy_callback
    )
    result = ex.check_git_status()
    assert result is True
    assert dummy_tracker.stash_called is True
    # Check that output_callback was invoked
    assert callback_called is True


def test_check_git_status_dirty_stash_failure(monkeypatch):
    # Setup: git enabled, repo status is DIRTY, action is 'stash', but stash fails
    dummy_tracker = DummyGitTracker(status=DummyGitStatus.DIRTY, stash_success=False)
    monkeypatch.setattr(exchange, "GitTracker", lambda: dummy_tracker)
    exchange.config.git_config.dirty_repo_action = "stash"

    ex = Exchange("chat_dirty_stash_fail", {"content": "Test"})
    result = ex.check_git_status()
    assert result is False


def test_complete_sets_assistant_and_tool_calls(monkeypatch):
    # Setup a dummy tracker to simulate a clean repo (so commit_changes won't commit)
    dummy_tracker = DummyGitTracker(status=DummyGitStatus.CLEAN)
    monkeypatch.setattr(exchange, "GitTracker", lambda: dummy_tracker)

    ex = Exchange("chat_complete", {"role": "user", "content": "User message"})
    assistant = {"role": "assistant", "content": "Assistant reply"}
    tool_calls = ["tool1", "tool2"]
    ex.complete(assistant, tool_calls)
    assert ex.assistant_message["role"] == "assistant"
    assert ex.assistant_message["content"] == "Assistant reply"
    assert ex.tool_calls == tool_calls


def test_commit_changes_not_enabled(monkeypatch):
    # Test when git is disabled
    exchange.config.git_config.enabled = False
    ex = Exchange("chat_no_git", {"content": "Test"})
    result = ex.commit_changes()
    assert result is False
    # Reset for other tests
    exchange.config.git_config.enabled = True


def test_commit_changes_dirty_auto_commit_success(monkeypatch):
    dummy_tracker = DummyGitTracker(
        status=DummyGitStatus.DIRTY, auto_commit_success=True
    )
    monkeypatch.setattr(exchange, "GitTracker", lambda: dummy_tracker)

    ex = Exchange("chat_commit_success", {"content": "Test"})
    result = ex.commit_changes()
    assert result is True
    assert dummy_tracker.auto_commit_called is True


def test_commit_changes_dirty_auto_commit_failure(monkeypatch):
    dummy_tracker = DummyGitTracker(
        status=DummyGitStatus.DIRTY, auto_commit_success=False
    )
    monkeypatch.setattr(exchange, "GitTracker", lambda: dummy_tracker)

    ex = Exchange("chat_commit_fail", {"content": "Test"})
    result = ex.commit_changes()
    assert result is False
    assert dummy_tracker.auto_commit_called is True


def test_to_messages_without_assistant():
    ex = Exchange("chat_msgs", {"content": "User message"})
    msgs = ex.to_messages()
    assert len(msgs) == 1
    assert msgs[0]["content"] == "User message"


def test_to_messages_with_assistant():
    ex = Exchange("chat_msgs2", {"content": "User message"})
    # Complete exchange with assistant message
    ex.complete({"content": "Assistant message"})
    msgs = ex.to_messages()
    assert len(msgs) == 2
    contents = [m["content"] for m in msgs]
    assert "User message" in contents
    assert "Assistant message" in contents


def test_get_duration(monkeypatch):
    ex = Exchange("chat_duration", {"content": "Test"})
    # simulate a duration by manually setting started_at and completed_at
    ex.started_at = datetime.now() - timedelta(seconds=5)
    ex.completed_at = datetime.now()
    dur = ex.get_duration()
    assert dur >= 5


def test_get_tool_call_count():
    ex = Exchange("chat_tool_calls", {"content": "Test"})
    ex.tool_calls = ["tool1", "tool2", "tool3"]
    count = ex.get_tool_call_count()
    assert count == 3


def test_get_exchange_summary(monkeypatch):
    # Test summary includes git commit result
    dummy_tracker = DummyGitTracker(
        status=DummyGitStatus.DIRTY, auto_commit_success=True
    )
    monkeypatch.setattr(exchange, "GitTracker", lambda: dummy_tracker)
    exchange.config.git_config.dirty_repo_action = "stop"
    ex = Exchange("chat_summary", {"content": "Test"})
    # Complete the exchange to set completed_at
    ex.complete({"content": "Assistant"}, tool_calls=["tool1"])
    summary = ex.get_exchange_summary()
    assert summary["chat_id"] == "chat_summary"
    assert summary["completed_at"] is not None
    # Since in our dummy tracker commit_changes() will trigger auto_commit and return True
    assert summary["git_changes_committed"] is True


def test_commit_changes_exception(monkeypatch):
    # Test that if commit_changes fails inside complete, exchange still completes
    def failing_commit_changes():
        raise Exception("Commit error")

    ex = Exchange("chat_exception", {"content": "Test"})
    monkeypatch.setattr(ex, "commit_changes", failing_commit_changes)
    # This should not raise despite exception in commit_changes
    ex.complete({"content": "Assistant after exception"})
    # Check that assistant_message is set regardless of commit failure
    assert ex.assistant_message["content"] == "Assistant after exception"
