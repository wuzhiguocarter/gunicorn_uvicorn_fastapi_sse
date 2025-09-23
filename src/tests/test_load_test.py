"""
Test cases for load testing utilities
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.load_test.client import TestMetrics, ChatBotLoadTester


class TestTestMetrics:
    """Test cases for TestMetrics"""

    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = TestMetrics()
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.total_response_time == 0.0
        assert metrics.min_response_time == float('inf')
        assert metrics.max_response_time == 0.0
        assert len(metrics.response_times) == 0
        assert len(metrics.errors) == 0

    def test_add_response_time(self):
        """Test adding response time"""
        metrics = TestMetrics()
        metrics.add_response_time(0.5)
        metrics.add_response_time(1.0)
        metrics.add_response_time(0.3)

        assert len(metrics.response_times) == 3
        assert metrics.total_response_time == 1.8
        assert metrics.min_response_time == 0.3
        assert metrics.max_response_time == 1.0

    def test_average_response_time(self):
        """Test average response time calculation"""
        metrics = TestMetrics()
        assert metrics.average_response_time == 0.0

        metrics.add_response_time(0.5)
        metrics.add_response_time(1.0)
        assert metrics.average_response_time == 0.75

    def test_success_rate(self):
        """Test success rate calculation"""
        metrics = TestMetrics()
        assert metrics.success_rate == 0.0

        metrics.total_requests = 10
        metrics.successful_requests = 8
        assert metrics.success_rate == 80.0

    def test_throughput(self):
        """Test throughput calculation"""
        metrics = TestMetrics()
        assert metrics.throughput == 0.0

        metrics.start_time = 1000.0
        metrics.end_time = 1002.0
        metrics.total_requests = 20
        assert metrics.throughput == 10.0

    def test_add_error(self):
        """Test adding error"""
        metrics = TestMetrics()
        error = Exception("Test error")
        metrics.add_error(error, {"message": "test"})

        assert metrics.failed_requests == 1
        assert len(metrics.errors) == 1
        assert metrics.errors[0]["error"] == "Test error"
        assert metrics.errors[0]["type"] == "Exception"

    def test_to_dict(self):
        """Test converting metrics to dictionary"""
        metrics = TestMetrics()
        metrics.start_time = 1000.0
        metrics.end_time = 1002.0
        metrics.total_requests = 10
        metrics.successful_requests = 8
        metrics.failed_requests = 2
        metrics.add_response_time(0.5)
        metrics.add_response_time(1.0)

        result = metrics.to_dict()
        assert result["total_requests"] == 10
        assert result["successful_requests"] == 8
        assert result["failed_requests"] == 2
        assert result["success_rate"] == 80.0
        assert result["average_response_time"] == 0.75
        assert result["throughput"] == 5.0
        assert result["total_duration"] == 2.0


class TestChatBotLoadTester:
    """Test cases for ChatBotLoadTester"""

    @pytest.fixture
    def tester(self):
        """Create a load tester instance"""
        return ChatBotLoadTester("http://test.example.com")

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        async with ChatBotLoadTester("http://test.example.com") as tester:
            assert tester.session is not None
            assert tester.base_url == "http://test.example.com"

        # Session should be closed after context exit
        assert tester.session.closed

    @pytest.mark.asyncio
    async def test_health_check_success(self, tester):
        """Test successful health check"""
        async with tester:
            with patch.object(tester.session, 'get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await tester.health_check()
                assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, tester):
        """Test failed health check"""
        async with tester:
            with patch.object(tester.session, 'get') as mock_get:
                mock_get.side_effect = Exception("Connection error")

                result = await tester.health_check()
                assert result is False

    @pytest.mark.asyncio
    async def test_send_single_request_success(self, tester):
        """Test successful single request"""
        async with tester:
            # Mock the session and response
            with patch.object(tester.session, 'post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status = 200

                # Mock SSE stream
                mock_content = AsyncMock()
                mock_content.__aiter__.return_value = [
                    b'data: {"type": "connected", "conversation_id": "test"}\n',
                    b'data: {"type": "partial_response", "content": "Hello"}\n',
                    b'data: {"type": "complete", "content": "Hello"}\n',
                ]
                mock_response.content = mock_content
                mock_post.return_value.__aenter__.return_value = mock_response

                result = await tester.send_single_request("Hello")

                assert result["success"] is True
                assert result["response_time"] > 0
                assert result["event_count"] == 3
                assert result["message_length"] > 0

    @pytest.mark.asyncio
    async def test_send_single_request_http_error(self, tester):
        """Test single request with HTTP error"""
        async with tester:
            with patch.object(tester.session, 'post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status = 500
                mock_response.text = AsyncMock(return_value="Server Error")
                mock_post.return_value.__aenter__.return_value = mock_response

                result = await tester.send_single_request("Hello")

                assert result["success"] is False
                assert "HTTP 500" in result["error"]

    @pytest.mark.asyncio
    async def test_send_single_request_connection_error(self, tester):
        """Test single request with connection error"""
        async with tester:
            with patch.object(tester.session, 'post') as mock_post:
                mock_post.side_effect = Exception("Connection failed")

                result = await tester.send_single_request("Hello")

                assert result["success"] is False
                assert "Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_run_concurrent_test(self, tester):
        """Test concurrent load test"""
        async with tester:
            # Mock send_single_request to return success and increment metrics
            async def mock_send_request(*args, **kwargs):
                tester.metrics.total_requests += 1
                tester.metrics.successful_requests += 1
                tester.metrics.add_response_time(0.5)
                return {
                    "success": True,
                    "response_time": 0.5,
                    "event_count": 3,
                    "message_length": 10,
                }

            with patch.object(tester, 'send_single_request', side_effect=mock_send_request):
                results = await tester.run_concurrent_test(
                    num_requests=10,
                    concurrency=2,
                    multi_turn=False
                )

                assert "results" in results
                assert "metrics" in results
                assert len(results["results"]) == 10
                assert results["metrics"]["total_requests"] == 10
                assert results["metrics"]["successful_requests"] == 10

    @pytest.mark.asyncio
    async def test_run_concurrent_test_with_errors(self, tester):
        """Test concurrent load test with errors"""
        async with tester:
            # Mock send_single_request to simulate success and failure
            request_count = 0

            async def mock_send_request(*args, **kwargs):
                nonlocal request_count
                request_count += 1
                if request_count <= 2:  # First 2 requests succeed
                    tester.metrics.total_requests += 1
                    tester.metrics.successful_requests += 1
                    tester.metrics.add_response_time(0.5)
                    return {"success": True, "response_time": 0.5, "event_count": 3, "message_length": 10}
                else:  # Last 2 requests fail
                    tester.metrics.total_requests += 1
                    tester.metrics.add_error(Exception("Test error"))
                    return {"success": False, "response_time": 0.2, "error": "Test error"}

            with patch.object(tester, 'send_single_request', side_effect=mock_send_request):
                results = await tester.run_concurrent_test(
                    num_requests=4,
                    concurrency=2,
                    multi_turn=False
                )

                assert results["metrics"]["total_requests"] == 4
                assert results["metrics"]["successful_requests"] == 2
                assert results["metrics"]["failed_requests"] == 2
                assert results["metrics"]["success_rate"] == 50.0
                assert len(results["metrics"]["errors"]) == 2

    @pytest.mark.asyncio
    async def test_get_metrics_success(self, tester):
        """Test getting server metrics successfully"""
        async with tester:
            with patch.object(tester.session, 'get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={"total_requests": 100})
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await tester.get_metrics()
                assert result == {"total_requests": 100}

    @pytest.mark.asyncio
    async def test_get_metrics_failure(self, tester):
        """Test getting server metrics when it fails"""
        async with tester:
            with patch.object(tester.session, 'get') as mock_get:
                mock_get.side_effect = Exception("Connection error")

                result = await tester.get_metrics()
                assert result == {}