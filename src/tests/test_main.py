"""
Test cases for the main FastAPI application
"""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.app.main import app


class TestMainApp:
    """Test cases for the main FastAPI application"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        with TestClient(app) as test_client:
            yield test_client

    def test_root_endpoint(self, client):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "ChatBot SSE Server" in response.text

    def test_health_check_endpoint(self, client):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
        assert "active_connections" in data

    def test_metrics_endpoint(self, client):
        """Test the metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "total_requests" in data
        assert "active_conversations" in data
        assert "average_response_time" in data
        assert "error_rate" in data
        assert "timestamp" in data

    def test_chat_endpoint_success(self, client):
        """Test successful chat endpoint"""
        with patch('src.app.main.chatbot') as mock_chatbot:
            # Mock chatbot stream
            async def mock_stream():
                yield MagicMock(event="connected", data='{"conversation_id": "test"}')
                yield MagicMock(event="message", data='{"content": "Hello"}')
                yield MagicMock(event="completed", data='{"message_id": "test"}')

            mock_chatbot.stream_chat.return_value = mock_stream()

            response = client.post(
                "/chat",
                data={"message": "Hello"},
                headers={"content-type": "application/x-www-form-urlencoded"}
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

    def test_chat_endpoint_no_message(self, client):
        """Test chat endpoint with no message"""
        response = client.post(
            "/chat",
            data={},
            headers={"content-type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 422

    def test_chat_endpoint_empty_message(self, client):
        """Test chat endpoint with empty message"""
        response = client.post(
            "/chat",
            data={"message": ""},
            headers={"content-type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 422

    def test_conversation_history_endpoint(self, client):
        """Test conversation history endpoint"""
        conv_id = "test-conversation-id"

        with patch('src.app.main.chatbot') as mock_chatbot:
            # Mock chatbot response
            mock_chatbot.get_conversation_history = AsyncMock(return_value=[
                {
                    "id": "test-id",
                    "content": "Hello",
                    "role": "user",
                    "timestamp": "2023-01-01T00:00:00",
                    "metadata": {}
                }
            ])

            response = client.get(f"/conversations/{conv_id}/history")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["content"] == "Hello"

    def test_conversation_history_endpoint_with_limit(self, client):
        """Test conversation history endpoint with limit"""
        conv_id = "test-conversation-id"

        with patch('src.app.main.chatbot') as mock_chatbot:
            # Mock chatbot response
            mock_chatbot.get_conversation_history = AsyncMock(return_value=[])

            response = client.get(f"/conversations/{conv_id}/history?limit=5")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_conversation_history_endpoint_error(self, client):
        """Test conversation history endpoint with error"""
        conv_id = "test-conversation-id"

        with patch('src.app.main.chatbot') as mock_chatbot:
            # Mock chatbot to raise an exception
            mock_chatbot.get_conversation_history.side_effect = Exception("Test error")

            response = client.get(f"/conversations/{conv_id}/history")

            assert response.status_code == 500

    def test_metrics_middleware(self, client):
        """Test that metrics middleware tracks requests"""
        # Make some requests
        client.get("/health")
        client.get("/health")

        response = client.get("/metrics")
        data = response.json()

        # Should have at least 2 requests (the health checks)
        assert data["total_requests"] >= 2

    def test_cors_middleware(self, client):
        """Test CORS middleware"""
        response = client.options("/chat", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        })

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers