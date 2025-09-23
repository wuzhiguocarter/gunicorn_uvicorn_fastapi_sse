"""
ChatBot implementation with SSE support
"""

import asyncio
import json
from typing import AsyncGenerator, Optional

from fastapi import HTTPException, status
from sse_starlette.sse import EventSourceResponse

from .config import settings
from .conversation_manager import conversation_manager
from .logger import get_logger
from .models import ChatRequest, ChatResponse, Message, SSEEvent

logger = get_logger(__name__)


class ChatBot:
    """ChatBot with SSE streaming support"""

    def __init__(self):
        self.response_delay = settings.response_delay
        self.max_history_length = settings.max_history_length

    async def generate_response(
        self, user_message: str, conversation_history: list[Message]
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response"""
        # Simulate AI response generation
        responses = [
            f"收到您的消息：{user_message}",
            "我正在思考如何回复...",
            "这是一个基于 SSE 的流式回复示例",
            "回复内容会分块发送给您",
            "感谢您的耐心等待！",
        ]

        for i, response in enumerate(responses):
            # Simulate processing delay
            await asyncio.sleep(self.response_delay)

            # Send partial response
            data = {
                "type": "partial_response",
                "content": response,
                "progress": (i + 1) / len(responses),
                "conversation_history_length": len(conversation_history),
            }

            yield json.dumps(data, ensure_ascii=False)

        # Send completion event
        complete_data = {
            "type": "complete",
            "content": responses[-1],
            "total_tokens": sum(len(r) for r in responses),
            "conversation_history_length": len(conversation_history),
        }

        yield json.dumps(complete_data, ensure_ascii=False)

    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[SSEEvent, None]:
        """Stream chat response via SSE"""
        try:
            # Get or create conversation
            if request.conversation_id:
                conversation = await conversation_manager.get_conversation(request.conversation_id)
                if not conversation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Conversation not found",
                    )
            else:
                conversation = await conversation_manager.create_conversation()

            # Register connection
            await conversation_manager.register_connection(conversation.id)

            # Create user message
            user_message = Message(
                content=request.message,
                role="user",
                metadata=request.metadata,
            )

            # Add user message to conversation
            await conversation_manager.add_message(conversation.id, user_message)

            # Send connection established event
            yield SSEEvent(
                event="connected",
                data=json.dumps(
                    {
                        "conversation_id": str(conversation.id),
                        "message_id": str(user_message.id),
                        "status": "connected",
                    },
                    ensure_ascii=False,
                ),
            )

            # Generate and stream response
            async for response_chunk in self.generate_response(
                user_message.content, conversation.messages
            ):
                yield SSEEvent(
                    event="message",
                    data=response_chunk,
                )

            # Create assistant message
            response_data = json.loads(response_chunk)
            assistant_message = Message(
                content=response_data["content"],
                role="assistant",
                metadata={"total_tokens": response_data.get("total_tokens", 0)},
            )

            # Add assistant message to conversation
            await conversation_manager.add_message(conversation.id, assistant_message)

            # Send completion event
            yield SSEEvent(
                event="completed",
                data=json.dumps(
                    {
                        "conversation_id": str(conversation.id),
                        "message_id": str(assistant_message.id),
                        "message_content": assistant_message.content,
                        "total_messages": len(conversation.messages),
                    },
                    ensure_ascii=False,
                ),
            )

        except Exception as e:
            logger.error("chat_stream_error", error=str(e))
            yield SSEEvent(
                event="error",
                data=json.dumps(
                    {"error": str(e), "type": "stream_error"},
                    ensure_ascii=False,
                ),
            )
        finally:
            # Unregister connection
            if 'conversation' in locals() and conversation is not None:
                await conversation_manager.unregister_connection(conversation.id)

    async def get_conversation_history(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> list[dict]:
        """Get conversation history"""
        try:
            conv_id = conversation_id
            messages = await conversation_manager.get_conversation_history(conv_id, limit)
            if messages is None:
                return []

            return [
                {
                    "id": str(msg.id),
                    "content": msg.content,
                    "role": msg.role,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error("get_history_error", error=str(e), conversation_id=conversation_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve conversation history",
            )


# Global ChatBot instance
chatbot = ChatBot()