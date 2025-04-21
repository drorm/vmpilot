"""
Simplified unit tests for the database module.
"""

import unittest

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from vmpilot.db.crud import ConversationRepository


class TestConversationRepository(unittest.TestCase):
    """Simplified test cases for the ConversationRepository class."""

    def test_serialize_deserialize_messages(self):
        """Test that messages can be serialized and deserialized correctly."""
        print("Starting test_serialize_deserialize_messages")

        # Create a repository
        repo = ConversationRepository()

        # Sample messages for testing
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Hello, how are you?"),
            AIMessage(content="I'm doing well, thank you for asking!"),
        ]

        # Serialize messages
        print("Serializing messages")
        serialized = repo.serialize_messages(messages)
        print(f"Serialized: {serialized[:50]}...")

        # Deserialize messages
        print("Deserializing messages")
        deserialized = repo.deserialize_messages(serialized)
        print(f"Deserialized {len(deserialized)} messages")

        # Verify that deserialized messages match original messages
        self.assertEqual(len(deserialized), 3)
        self.assertEqual(deserialized[0].content, messages[0].content)
        self.assertEqual(deserialized[1].content, messages[1].content)
        self.assertEqual(deserialized[2].content, messages[2].content)


if __name__ == "__main__":
    unittest.main()
