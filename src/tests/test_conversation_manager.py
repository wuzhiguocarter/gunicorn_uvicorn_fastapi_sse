"""
Test cases for conversation manager
"""

from uuid import uuid4

import pytest

from src.app.conversation_manager import ConversationManager
from src.app.models import Message


class TestConversationManager:
    """Test cases for ConversationManager"""

    @pytest.fixture
    def manager(self):
        """Create a conversation manager for testing"""
        return ConversationManager(max_history_length=5)

    @pytest.mark.asyncio
    async def test_create_conversation(self, manager):
        """Test conversation creation"""
        conversation = await manager.create_conversation()
        assert conversation.id is not None
        assert len(conversation.messages) == 0
        assert conversation in manager._conversations.values()

    @pytest.mark.asyncio
    async def test_get_conversation(self, manager):
        """Test getting conversation"""
        # Create conversation
        conversation = await manager.create_conversation()

        # Get conversation
        retrieved = await manager.get_conversation(conversation.id)
        assert retrieved == conversation

        # Get non-existent conversation
        non_existent = await manager.get_conversation(uuid4())
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_add_message(self, manager):
        """Test adding message to conversation"""
        # Create conversation
        conversation = await manager.create_conversation()

        # Add message
        message = Message(content="Hello", role="user")
        result = await manager.add_message(conversation.id, message)

        assert result is not None
        assert len(result.messages) == 1
        assert result.messages[0] == message

        # Add message to non-existent conversation
        result = await manager.add_message(uuid4(), message)
        assert result is None

    @pytest.mark.asyncio
    async def test_history_limit(self, manager):
        """Test history limit enforcement"""
        conversation = await manager.create_conversation()

        # Add more messages than the limit
        for i in range(10):
            message = Message(content=f"Message {i}", role="user")
            await manager.add_message(conversation.id, message)

        # Should be limited to max_history_length
        assert len(conversation.messages) == 5
        assert conversation.messages[0].content == "Message 5"
        assert conversation.messages[-1].content == "Message 9"

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, manager):
        """Test getting conversation history"""
        conversation = await manager.create_conversation()

        # Add messages
        for i in range(3):
            message = Message(content=f"Message {i}", role="user")
            await manager.add_message(conversation.id, message)

        # Get full history
        history = await manager.get_conversation_history(conversation.id)
        assert len(history) == 3

        # Get limited history
        limited_history = await manager.get_conversation_history(
            conversation.id, limit=2
        )
        assert len(limited_history) == 2
        assert limited_history[0].content == "Message 1"
        assert limited_history[1].content == "Message 2"

        # Get history for non-existent conversation
        non_existent_history = await manager.get_conversation_history(uuid4())
        assert non_existent_history is None

    @pytest.mark.asyncio
    async def test_connection_tracking(self, manager):
        """Test connection tracking"""
        conversation = await manager.create_conversation()

        # Register connection
        await manager.register_connection(conversation.id)
        assert manager._active_connections[conversation.id] == 1

        # Register another connection
        await manager.register_connection(conversation.id)
        assert manager._active_connections[conversation.id] == 2

        # Unregister connection
        await manager.unregister_connection(conversation.id)
        assert manager._active_connections[conversation.id] == 1

        # Unregister last connection
        await manager.unregister_connection(conversation.id)
        assert conversation.id not in manager._active_connections

    @pytest.mark.asyncio
    async def test_metrics(self, manager):
        """Test metrics collection"""
        # Get initial metrics
        initial_metrics = await manager.get_metrics()
        assert initial_metrics["total_conversations"] == 0
        assert initial_metrics["total_messages"] == 0
        assert initial_metrics["active_conversations"] == 0

        # Create conversation
        conversation = await manager.create_conversation()

        # Add message
        message = Message(content="Hello", role="user")
        await manager.add_message(conversation.id, message)

        # Register connection
        await manager.register_connection(conversation.id)

        # Get updated metrics
        metrics = await manager.get_metrics()
        assert metrics["total_conversations"] == 1
        assert metrics["total_messages"] == 1
        assert metrics["active_conversations"] == 1
        assert metrics["active_connections"] == 1

    @pytest.mark.asyncio
    async def test_cleanup_inactive_conversations(self, manager):
        """Test cleanup of inactive conversations"""
        # Create multiple conversations
        conversations = []
        for _i in range(3):
            conv = await manager.create_conversation()
            conversations.append(conv)

        # Add messages to first conversation
        message = Message(content="Hello", role="user")
        await manager.add_message(conversations[0].id, message)

        # Mock the updated_at to be very old
        import time

        old_time = time.time() - (25 * 3600)  # 25 hours ago
        conversations[1].updated_at = type(conversations[1].updated_at).fromtimestamp(
            old_time
        )
        conversations[2].updated_at = type(conversations[2].updated_at).fromtimestamp(
            old_time
        )

        # Update in manager
        manager._conversations[conversations[1].id] = conversations[1]
        manager._conversations[conversations[2].id] = conversations[2]

        # Cleanup old conversations
        await manager.cleanup_inactive_conversations(max_age_hours=24)

        # Should have only one conversation left
        assert len(manager._conversations) == 1
        assert conversations[0].id in manager._conversations
        assert conversations[1].id not in manager._conversations
        assert conversations[2].id not in manager._conversations

    @pytest.mark.asyncio
    async def test_get_active_conversation_count(self, manager):
        """Test getting active conversation count"""
        # Initially no active conversations
        count = await manager.get_active_conversation_count()
        assert count == 0

        # Create conversation and register connection
        conversation = await manager.create_conversation()
        await manager.register_connection(conversation.id)

        # Should have one active conversation
        count = await manager.get_active_conversation_count()
        assert count == 1

        # Create another conversation without connection
        conversation2 = await manager.create_conversation()

        # Still only one active conversation
        count = await manager.get_active_conversation_count()
        assert count == 1

        # Register connection to second conversation
        await manager.register_connection(conversation2.id)

        # Should have two active conversations
        count = await manager.get_active_conversation_count()
        assert count == 2
