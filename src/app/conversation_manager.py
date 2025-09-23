"""
Conversation management for the ChatBot SSE Server
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, Optional
from uuid import UUID

from .logger import get_logger
from .models import Conversation, Message

logger = get_logger(__name__)


class ConversationManager:
    """Manages conversation state and history"""

    def __init__(self, max_history_length: int = 10):
        self._conversations: Dict[UUID, Conversation] = {}
        self._max_history_length = max_history_length
        self._active_connections: Dict[UUID, int] = defaultdict(int)
        self._metrics = {
            "total_conversations": 0,
            "total_messages": 0,
            "start_time": time.time(),
        }

    async def create_conversation(self) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation()
        self._conversations[conversation.id] = conversation
        self._metrics["total_conversations"] += 1
        logger.info("conversation_created", conversation_id=str(conversation.id))
        return conversation

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get a conversation by ID"""
        return self._conversations.get(conversation_id)

    async def add_message(
        self, conversation_id: UUID, message: Message
    ) -> Optional[Conversation]:
        """Add a message to a conversation"""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None

        # Limit conversation history
        if len(conversation.messages) >= self._max_history_length:
            conversation.messages = conversation.messages[-self._max_history_length + 1 :]

        conversation.add_message(message)
        self._metrics["total_messages"] += 1
        logger.info("message_added", conversation_id=str(conversation_id), message_id=str(message.id))
        return conversation

    async def get_conversation_history(
        self, conversation_id: UUID, limit: Optional[int] = None
    ) -> Optional[list[Message]]:
        """Get conversation history"""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None

        messages = conversation.messages
        if limit:
            messages = messages[-limit:]
        return messages

    async def register_connection(self, conversation_id: UUID) -> None:
        """Register a new connection for a conversation"""
        self._active_connections[conversation_id] += 1
        logger.debug("connection_registered", conversation_id=str(conversation_id))

    async def unregister_connection(self, conversation_id: UUID) -> None:
        """Unregister a connection for a conversation"""
        if conversation_id in self._active_connections:
            self._active_connections[conversation_id] -= 1
            if self._active_connections[conversation_id] <= 0:
                del self._active_connections[conversation_id]
            logger.debug("connection_unregistered", conversation_id=str(conversation_id))

    async def get_metrics(self) -> dict:
        """Get system metrics"""
        uptime = time.time() - self._metrics["start_time"]
        return {
            "total_conversations": self._metrics["total_conversations"],
            "total_messages": self._metrics["total_messages"],
            "active_conversations": len(self._active_connections),
            "active_connections": sum(self._active_connections.values()),
            "uptime_seconds": uptime,
        }

    async def cleanup_inactive_conversations(self, max_age_hours: int = 24) -> None:
        """Clean up old conversations"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)

        to_remove = []
        for conv_id, conversation in self._conversations.items():
            if conversation.updated_at.timestamp() < cutoff_time:
                to_remove.append(conv_id)

        for conv_id in to_remove:
            del self._conversations[conv_id]
            if conv_id in self._active_connections:
                del self._active_connections[conv_id]
            logger.info("conversation_cleaned_up", conversation_id=str(conv_id))

    async def get_active_conversation_count(self) -> int:
        """Get count of active conversations"""
        return len(self._active_connections)


# Global conversation manager instance
conversation_manager = ConversationManager()