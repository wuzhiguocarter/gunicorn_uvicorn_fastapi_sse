"""
FastAPI application with SSE ChatBot
"""

import time
from contextlib import asynccontextmanager
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, Form, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from .chatbot import chatbot
from .config import settings
from .conversation_manager import conversation_manager
from .logger import get_logger, setup_logging
from .models import ChatRequest, HealthResponse, MetricsResponse, Message, Conversation

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("application_startup")
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title="ChatBot SSE Server",
    description="A ChatBot server with Server-Sent Events support",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global metrics
startup_time = time.time()
request_count = 0
error_count = 0


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect metrics"""
    global request_count, error_count
    request_count += 1
    start_time = time.time()

    try:
        response = await call_next(request)
        return response
    except Exception as e:
        error_count += 1
        raise e
    finally:
        process_time = time.time() - start_time
        logger.info(
            "request_processed",
            method=request.method,
            path=request.url.path,
            process_time=process_time,
        )


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with simple HTML test client"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatBot SSE Server</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .chat-container { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; margin-bottom: 20px; }
            .message { margin-bottom: 10px; padding: 10px; border-radius: 5px; }
            .user { background-color: #e3f2fd; text-align: right; }
            .assistant { background-color: #f5f5f5; }
            .input-container { display: flex; gap: 10px; }
            input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
            button { padding: 10px 20px; background-color: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background-color: #1976D2; }
            .status { margin-bottom: 10px; padding: 5px; border-radius: 3px; }
            .connected { background-color: #c8e6c9; }
            .error { background-color: #ffcdd2; }
        </style>
    </head>
    <body>
        <h1>ChatBot SSE Server</h1>
        <div id="status" class="status">Not connected</div>
        <div id="chat-container" class="chat-container"></div>
        <div class="input-container">
            <input type="text" id="message-input" placeholder="Type your message..." />
            <button onclick="sendMessage()">Send</button>
        </div>

        <script>
            let eventSource = null;
            let conversationId = null;
            let currentBotMessage = null;
            const statusDiv = document.getElementById('status');
            const chatContainer = document.getElementById('chat-container');
            const messageInput = document.getElementById('message-input');

            function updateStatus(message, isError = false) {
                statusDiv.textContent = message;
                statusDiv.className = isError ? 'status error' : 'status connected';
            }

            function addMessage(content, isUser = false) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
                messageDiv.textContent = content;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;

                addMessage(message, true);
                messageInput.value = '';

                const formData = new FormData();
                formData.append('message', message);
                if (conversationId) {
                    formData.append('conversation_id', conversationId);
                }

                fetch('/chat', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.body;
                })
                .then(body => {
                    const reader = body.getReader();
                    const decoder = new TextDecoder();

                    function readChunk() {
                        return reader.read().then(({ done, value }) => {
                            if (done) return;

                            const chunk = decoder.decode(value);
                            const lines = chunk.split('\\n');

                            let currentEvent = '';
                            let currentData = '';

                            lines.forEach(line => {
                                line = line.trim();
                                if (line.startsWith('event: ')) {
                                    currentEvent = line.slice(7);
                                } else if (line.startsWith('data: ')) {
                                    currentData = line.slice(6);
                                    try {
                                        const data = JSON.parse(currentData);
                                        data.event = currentEvent; // Add event type to data
                                        handleSSEData(data);
                                    } catch (e) {
                                        console.error('Error parsing SSE data:', e);
                                    }
                                } else if (line === '') {
                                    // Empty line indicates end of event
                                    currentEvent = '';
                                    currentData = '';
                                }
                            });

                            return readChunk();
                        });
                    }

                    return readChunk();
                })
                .catch(error => {
                    updateStatus('Error: ' + error.message, true);
                    console.error('Error:', error);
                });
            }

            function handleSSEData(data) {
                if (data.event === 'connected') {
                    conversationId = data.conversation_id;
                    updateStatus('Connected');
                } else if (data.event === 'message') {
                    // Check if this is a partial response or a message with content
                    if (data.content) {
                        // If this is a new message, create a new message element
                        if (!currentBotMessage) {
                            currentBotMessage = document.createElement('div');
                            currentBotMessage.className = 'message assistant';
                            chatContainer.appendChild(currentBotMessage);
                        }
                        currentBotMessage.textContent += data.content;
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                } else if (data.event === 'completed') {
                    updateStatus('Message complete');
                    currentBotMessage = null; // Reset for next message
                } else if (data.event === 'error') {
                    updateStatus('Error: ' + data.error, true);
                    currentBotMessage = null;
                }
            }

            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """


@app.post("/chat")
async def chat_endpoint(
    message: str = Form(..., description="Message to send to the chatbot"),
    conversation_id: Optional[str] = Form(None, description="Optional conversation ID for multi-turn conversations"),
):
    """Chat endpoint with SSE streaming

    Sends a message to the chatbot and receives a streaming response via Server-Sent Events.

    Args:
        message: The message content (required, 1-1000 characters)
        conversation_id: Optional conversation ID to continue an existing conversation

    Returns:
        Server-Sent Events stream with response chunks

    SSE Events:
        - connected: Connection established with conversation_id
        - message: Partial response chunk with content
        - completed: Final response with summary
        - error: Error message if something goes wrong
    """
    try:
        if not message:
            raise HTTPException(status_code=422, detail="Message is required")

        # Convert conversation_id to UUID if provided
        conv_id = None
        if conversation_id:
            try:
                conv_id = UUID(conversation_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid conversation_id format")

        chat_request = ChatRequest(
            message=message,
            conversation_id=conv_id,
        )

        return EventSourceResponse(
            chatbot.stream_chat(chat_request),
            ping=30,  # Send ping every 30 seconds
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("chat_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint

    Returns:
        Health status including uptime, version, and active connections
    """
    uptime = time.time() - startup_time
    active_connections = await conversation_manager.get_active_conversation_count()

    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="0.1.0",
        uptime=uptime,
        active_connections=active_connections,
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics

    Returns:
        Performance metrics including request counts, error rates, and system stats
    """
    conversation_metrics = await conversation_manager.get_metrics()
    uptime = time.time() - startup_time
    error_rate = error_count / request_count if request_count > 0 else 0

    return MetricsResponse(
        total_requests=request_count,
        active_conversations=conversation_metrics["active_conversations"],
        average_response_time=0,  # TODO: Implement response time tracking
        error_rate=error_rate,
        timestamp=time.time(),
    )


@app.get("/conversations/{conversation_id}/history", response_model=List[dict])
async def get_conversation_history(
    conversation_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of messages to return")
):
    """Get conversation history for a specific conversation

    Args:
        conversation_id: The ID of the conversation
        limit: Optional limit on number of messages to return (1-100)

    Returns:
        List of message objects with content, role, and timestamp
    """
    try:
        return await chatbot.get_conversation_history(conversation_id, limit)
    except Exception as e:
        logger.error("conversation_history_error", error=str(e), conversation_id=conversation_id)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )