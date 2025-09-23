"""
Test cases for ChatBot
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.app.chatbot import ChatBot
from src.app.models import ChatRequest, Message


class TestChatBot:
    """Test cases for ChatBot"""

    @pytest.fixture
    def chatbot(self):
        """Create a chatbot instance for testing"""
        return ChatBot()

    @pytest.fixture
    def sample_message(self):
        """Create a sample message for testing"""
        return Message(content="Hello", role="user")

    @pytest.fixture
    def sample_conversation_history(self):
        """Create sample conversation history"""
        return [
            Message(content="Hello", role="user"),
            Message(content="Hi there", role="assistant"),
        ]

    @pytest.mark.asyncio
    async def test_generate_response(self, chatbot, sample_conversation_history):
        """Test response generation"""
        user_message = "How are you?"
        response_chunks = []

        async for chunk in chatbot.generate_response(user_message, sample_conversation_history):
            response_chunks.append(chunk)

        assert len(response_chunks) > 0
        assert any("收到您的消息" in chunk for chunk in response_chunks)
        assert any("complete" in json.loads(chunk)["type"] for chunk in response_chunks)

    @pytest.mark.asyncio
    async def test_stream_chat_new_conversation(self, chatbot, sample_message):
        """Test streaming chat with new conversation"""
        request = ChatRequest(message="Hello")
        sse_events = []

        with patch('src.app.chatbot.conversation_manager') as mock_manager:
            # Mock conversation manager methods
            mock_manager.create_conversation = AsyncMock()
            mock_manager.create_conversation.return_value = MagicMock(id=uuid4())
            mock_manager.get_conversation = AsyncMock(return_value=None)
            mock_manager.add_message = AsyncMock()
            mock_manager.register_connection = AsyncMock()
            mock_manager.unregister_connection = AsyncMock()

            async for event in chatbot.stream_chat(request):
                sse_events.append(event)

        # Should have multiple events
        assert len(sse_events) > 0
        assert any(event.event == "connected" for event in sse_events)
        assert any(event.event == "message" for event in sse_events)
        assert any(event.event == "completed" for event in sse_events)

    @pytest.mark.asyncio
    async def test_stream_chat_existing_conversation(self, chatbot, sample_message):
        """Test streaming chat with existing conversation"""
        conv_id = uuid4()
        request = ChatRequest(message="Hello", conversation_id=conv_id)
        sse_events = []

        with patch('src.app.chatbot.conversation_manager') as mock_manager:
            # Mock conversation manager methods
            mock_conversation = MagicMock()
            mock_conversation.id = conv_id
            mock_conversation.messages = []

            mock_manager.get_conversation = AsyncMock(return_value=mock_conversation)
            mock_manager.add_message = AsyncMock()
            mock_manager.register_connection = AsyncMock()
            mock_manager.unregister_connection = AsyncMock()

            async for event in chatbot.stream_chat(request):
                sse_events.append(event)

        assert len(sse_events) > 0
        assert any(event.event == "connected" for event in sse_events)

    @pytest.mark.asyncio
    async def test_stream_chat_nonexistent_conversation(self, chatbot):
        """Test streaming chat with non-existent conversation"""
        conv_id = uuid4()
        request = ChatRequest(message="Hello", conversation_id=conv_id)
        sse_events = []

        with patch('src.app.chatbot.conversation_manager') as mock_manager:
            # Mock conversation manager to return None for non-existent conversation
            mock_manager.get_conversation = AsyncMock(return_value=None)

            async for event in chatbot.stream_chat(request):
                sse_events.append(event)

        # Should have error event
        assert len(sse_events) > 0
        assert any(event.event == "error" for event in sse_events)

    @pytest.mark.asyncio
    async def test_stream_chat_error_handling(self, chatbot):
        """Test error handling in streaming chat"""
        request = ChatRequest(message="Hello")
        sse_events = []

        with patch('src.app.chatbot.conversation_manager') as mock_manager:
            # Mock conversation manager to raise an exception
            mock_manager.create_conversation = AsyncMock(side_effect=Exception("Test error"))

            async for event in chatbot.stream_chat(request):
                sse_events.append(event)

        # Should have error event
        assert len(sse_events) > 0
        assert any(event.event == "error" for event in sse_events)

    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self, chatbot):
        """Test getting conversation history successfully"""
        conv_id = str(uuid4())

        with patch('src.app.chatbot.conversation_manager') as mock_manager:
            # Mock conversation manager
            mock_messages = [
                MagicMock(id=uuid4(), content="Hello", role="user", timestamp=MagicMock()),
                MagicMock(id=uuid4(), content="Hi there", role="assistant", timestamp=MagicMock()),
            ]

            for msg in mock_messages:
                msg.id = str(msg.id)
                msg.timestamp.isoformat = MagicMock(return_value="2023-01-01T00:00:00")

            mock_manager.get_conversation_history = AsyncMock(return_value=mock_messages)

            history = await chatbot.get_conversation_history(conv_id)

            assert len(history) == 2
            assert history[0]["content"] == "Hello"
            assert history[1]["content"] == "Hi there"

    @pytest.mark.asyncio
    async def test_get_conversation_history_not_found(self, chatbot):
        """Test getting conversation history when not found"""
        conv_id = str(uuid4())

        with patch('src.app.chatbot.conversation_manager') as mock_manager:
            # Mock conversation manager to return None
            mock_manager.get_conversation_history = AsyncMock(return_value=None)

            history = await chatbot.get_conversation_history(conv_id)

            assert history == []

    @pytest.mark.asyncio
    async def test_get_conversation_history_with_limit(self, chatbot):
        """Test getting conversation history with limit"""
        conv_id = str(uuid4())

        with patch('src.app.chatbot.conversation_manager') as mock_manager:
            # Mock conversation manager - return only 3 messages when limit is 3
            mock_messages = [
                MagicMock(id=uuid4(), content=f"Message {i}", role="user", timestamp=MagicMock())
                for i in range(3)  # Return only 3 messages to simulate the limit
            ]

            for msg in mock_messages:
                msg.id = str(msg.id)
                msg.timestamp.isoformat = MagicMock(return_value="2023-01-01T00:00:00")

            mock_manager.get_conversation_history = AsyncMock(return_value=mock_messages)

            history = await chatbot.get_conversation_history(conv_id, limit=3)

            assert len(history) == 3

    @pytest.mark.asyncio
    async def test_get_conversation_history_error(self, chatbot):
        """Test error handling in getting conversation history"""
        conv_id = str(uuid4())

        with patch('src.app.chatbot.conversation_manager') as mock_manager:
            # Mock conversation manager to raise an exception
            mock_manager.get_conversation_history = AsyncMock(side_effect=Exception("Test error"))

            with pytest.raises(Exception):
                await chatbot.get_conversation_history(conv_id)