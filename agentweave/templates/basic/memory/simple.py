"""
Simple in-memory storage implementation.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SimpleMemory:
    """
    A simple in-memory storage implementation.
    This is the default memory type for basic agents.
    """

    def __init__(self):
        """Initialize the memory store."""
        self._memory = {}
        self._conversations = {}

    def add(self, key: str, value: Any, namespace: str = "default") -> None:
        """
        Add an item to memory.

        Args:
            key: The key to store the value under
            value: The value to store
            namespace: Optional namespace to organize memory
        """
        if namespace not in self._memory:
            self._memory[namespace] = {}

        self._memory[namespace][key] = {"value": value, "timestamp": time.time()}

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Retrieve an item from memory.

        Args:
            key: The key to retrieve
            namespace: The namespace to look in

        Returns:
            The stored value or None if not found
        """
        if namespace not in self._memory:
            return None

        item = self._memory[namespace].get(key)
        return item["value"] if item else None

    def add_message(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """
        Add a message to a conversation.

        Args:
            conversation_id: The ID of the conversation
            message: The message to add (dict with role, content, etc.)
        """
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = {
                "messages": [],
                "created_at": time.time(),
                "updated_at": time.time(),
            }

        self._conversations[conversation_id]["messages"].append(message)
        self._conversations[conversation_id]["updated_at"] = time.time()

    def get_messages(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: The ID of the conversation
            limit: Optional limit on the number of messages to return

        Returns:
            List of messages in the conversation
        """
        if conversation_id not in self._conversations:
            return []

        messages = self._conversations[conversation_id]["messages"]
        if limit:
            return messages[-limit:]
        return messages

    def list_conversations(self) -> List[Tuple[str, float, float]]:
        """
        List all conversations.

        Returns:
            List of tuples with (conversation_id, created_at, updated_at)
        """
        return [
            (conv_id, data["created_at"], data["updated_at"])
            for conv_id, data in self._conversations.items()
        ]

    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear a conversation's messages.

        Args:
            conversation_id: The ID of the conversation to clear

        Returns:
            True if successful, False if conversation not found
        """
        if conversation_id not in self._conversations:
            return False

        self._conversations[conversation_id]["messages"] = []
        self._conversations[conversation_id]["updated_at"] = time.time()
        return True

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: The ID of the conversation to delete

        Returns:
            True if successful, False if conversation not found
        """
        if conversation_id not in self._conversations:
            return False

        del self._conversations[conversation_id]
        return True


# Singleton instance
memory = SimpleMemory()
