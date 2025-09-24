"""
Test cases for data models
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.app.models import ChatRequest, ChatResponse, Conversation, Message


class TestMessage:
    """Test cases for Message model"""

    def test_message_creation(self):
        """Test message creation"""
        message = Message(content="Hello", role="user")
        assert message.content == "Hello"
        assert message.role == "user"
        assert isinstance(message.id, UUID)
        assert isinstance(message.timestamp, datetime)

    def test_message_with_metadata(self):
        """Test message with metadata"""
        metadata = {"source": "web", "language": "en"}
        message = Message(content="Hello", role="user", metadata=metadata)
        assert message.metadata == metadata


class TestConversation:
    """Test cases for Conversation model"""

    def test_conversation_creation(self):
        """Test conversation creation"""
        conversation = Conversation()
        assert len(conversation.messages) == 0
        assert isinstance(conversation.id, UUID)
        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.updated_at, datetime)

    def test_add_message(self):
        """Test adding message to conversation"""
        conversation = Conversation()
        message = Message(content="Hello", role="user")
        conversation.add_message(message)

        assert len(conversation.messages) == 1
        assert conversation.messages[0] == message
        assert conversation.updated_at > conversation.created_at

    def test_get_last_message(self):
        """Test getting last message"""
        conversation = Conversation()

        # Empty conversation
        assert conversation.get_last_message() is None

        # Add messages
        message1 = Message(content="Hello", role="user")
        message2 = Message(content="Hi there", role="assistant")
        conversation.add_message(message1)
        conversation.add_message(message2)

        last_message = conversation.get_last_message()
        assert last_message == message2

    def test_history_limit(self):
        """Test conversation history limit"""
        conversation = Conversation()

        # Add more than max_history_length messages
        for i in range(15):
            message = Message(content=f"Message {i}", role="user")
            conversation.add_message(message)

        # Should be limited to 10 messages
        assert len(conversation.messages) == 10
        assert (
            conversation.messages[0].content == "Message 5"
        )  # First message should be index 5
        assert (
            conversation.messages[-1].content == "Message 14"
        )  # Last message should be index 14


class TestChatRequest:
    """Test cases for ChatRequest model"""

    def test_chat_request_creation(self):
        """Test chat request creation"""
        request = ChatRequest(message="Hello")
        assert request.message == "Hello"
        assert request.conversation_id is None
        assert request.metadata == {}

    def test_chat_request_with_conversation_id(self):
        """Test chat request with conversation ID"""
        conv_id = uuid4()
        request = ChatRequest(message="Hello", conversation_id=conv_id)
        assert request.conversation_id == conv_id

    def test_chat_request_with_metadata(self):
        """Test chat request with metadata"""
        metadata = {"source": "web"}
        request = ChatRequest(message="Hello", metadata=metadata)
        assert request.metadata == metadata

    def test_message_validation(self):
        """Test message validation"""
        # Empty message should fail
        with pytest.raises(ValueError):
            ChatRequest(message="")

        # Too long message should fail
        with pytest.raises(ValueError):
            ChatRequest(message="x" * 1001)


class TestChatResponse:
    """Test cases for ChatResponse model"""

    def test_chat_response_creation(self):
        """Test chat response creation"""
        message = Message(content="Hello", role="assistant")
        conversation_id = uuid4()
        response = ChatResponse(message=message, conversation_id=conversation_id)
        assert response.message == message
        assert response.conversation_id == conversation_id
        assert response.is_complete is False
        assert response.metadata == {}

    def test_chat_response_complete(self):
        """Test complete chat response"""
        message = Message(content="Hello", role="assistant")
        conversation_id = uuid4()
        response = ChatResponse(
            message=message, conversation_id=conversation_id, is_complete=True
        )
        assert response.is_complete is True
