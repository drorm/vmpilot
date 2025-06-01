"""
Unit tests for the agent_memory module.
"""

import pytest

from vmpilot.agent_memory import (
    clear_conversation_state,
    conversation_states,
    get_conversation_state,
    save_conversation_state,
    update_cache_info,
)


@pytest.fixture
def clear_states():
    """Fixture to clear conversation states before and after tests"""
    # Clear states before test
    conversation_states.clear()
    yield
    # Clear states after test
    conversation_states.clear()


def test_save_and_get_conversation_state(clear_states):
    """Test saving and retrieving conversation state"""
    # Setup
    thread_id = "test_thread_1"
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]
    cache_info = {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50}

    # Execute
    save_conversation_state(thread_id, messages, cache_info)
    retrieved_messages, retrieved_cache_info = get_conversation_state(thread_id)

    # Assert
    assert len(retrieved_messages) == 2
    assert retrieved_messages[0]["content"] == "Hello"
    assert retrieved_messages[1]["content"] == "Hi there"
    assert retrieved_cache_info == cache_info


def test_save_without_cache_info(clear_states):
    """Test saving conversation state without providing cache info"""
    # Setup
    thread_id = "test_thread_2"
    messages = [{"role": "user", "content": "Test message"}]

    # Execute
    save_conversation_state(thread_id, messages)
    _, retrieved_cache_info = get_conversation_state(thread_id)

    # Assert
    assert retrieved_cache_info == {}


def test_save_preserves_existing_cache_info(clear_states):
    """Test that saving without cache_info preserves existing cache_info"""
    # Setup
    thread_id = "test_thread_3"
    messages = [{"role": "user", "content": "Initial message"}]
    cache_info = {"total_tokens": 50}

    # Initial save with cache_info
    save_conversation_state(thread_id, messages, cache_info)

    # Update messages without providing cache_info
    new_messages = messages + [{"role": "assistant", "content": "Response"}]
    save_conversation_state(thread_id, new_messages)

    # Retrieve
    _, retrieved_cache_info = get_conversation_state(thread_id)

    # Assert
    assert retrieved_cache_info == cache_info


def test_get_nonexistent_conversation(clear_states):
    """Test retrieving a conversation state that doesn't exist"""
    # Execute
    messages, cache_info = get_conversation_state("nonexistent_thread")

    # Assert
    assert messages == []
    assert cache_info == {}


def test_update_cache_info(clear_states):
    """Test updating only the cache info"""
    # Setup
    thread_id = "test_thread_4"
    messages = [{"role": "user", "content": "Test"}]
    initial_cache_info = {"total_tokens": 10}
    save_conversation_state(thread_id, messages, initial_cache_info)

    # Update cache info
    new_cache_info = {"total_tokens": 20, "prompt_tokens": 10}
    update_cache_info(thread_id, new_cache_info)

    # Retrieve
    retrieved_messages, retrieved_cache_info = get_conversation_state(thread_id)

    # Assert
    assert len(retrieved_messages) == 1
    assert retrieved_messages[0]["content"] == "Test"
    assert retrieved_cache_info == new_cache_info


def test_update_cache_info_nonexistent_thread(clear_states):
    """Test updating cache info for a thread that doesn't exist"""
    # Execute - should not raise an exception
    update_cache_info("nonexistent_thread", {"total_tokens": 50})

    # Verify no state was created
    messages, cache_info = get_conversation_state("nonexistent_thread")
    assert messages == []
    assert cache_info == {}


def test_clear_conversation_state(clear_states):
    """Test clearing a conversation state"""
    # Setup
    thread_id = "test_thread_5"
    messages = [{"role": "user", "content": "Test"}]
    save_conversation_state(thread_id, messages)

    # Execute
    clear_conversation_state(thread_id)

    # Verify
    messages, cache_info = get_conversation_state(thread_id)
    assert messages == []
    assert cache_info == {}


def test_none_thread_id_handling():
    """Test handling of None thread_id values"""
    # These operations should not raise exceptions
    save_conversation_state(None, [{"role": "user", "content": "Test"}])
    update_cache_info(None, {"total_tokens": 10})

    # Get with None should return empty state
    messages, cache_info = get_conversation_state(None)
    assert messages == []
    assert cache_info == {}

    # Clear with None should not raise an exception
    clear_conversation_state(None)  # Should not raise
