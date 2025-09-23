"""
Data models for the ChatBot SSE Server
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message model"""

    id: UUID = Field(default_factory=uuid4)
    content: str
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        pass


class Conversation(BaseModel):
    """Conversation model with message history"""

    id: UUID = Field(default_factory=uuid4)
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    max_history_length: int = 10

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation"""
        self.messages.append(message)
        # Enforce history limit
        if len(self.messages) > self.max_history_length:
            self.messages = self.messages[-self.max_history_length:]
        self.updated_at = datetime.now(timezone.utc)

    def get_last_message(self) -> Optional[Message]:
        """Get the last message in the conversation"""
        return self.messages[-1] if self.messages else None

    class Config:
        pass


class ChatRequest(BaseModel):
    """Chat request model"""

    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Chat response model"""

    message: Message
    conversation_id: UUID
    is_complete: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        pass


class SSEEvent(BaseModel):
    """SSE event model"""

    event: str
    data: str
    id: Optional[str] = None
    retry: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    timestamp: datetime
    version: str
    uptime: float
    active_connections: int


class MetricsResponse(BaseModel):
    """Performance metrics response model"""

    total_requests: int
    active_conversations: int
    average_response_time: float
    error_rate: float
    timestamp: datetime