"""
Load testing client for the ChatBot SSE Server
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

import aiohttp
from tqdm import tqdm


@dataclass
class TestMetrics:
    """Test metrics collector"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float("inf")
    max_response_time: float = 0.0
    response_times: list[float] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    start_time: float | None = None
    end_time: float | None = None

    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def throughput(self) -> float:
        """Calculate requests per second"""
        if not self.start_time or not self.end_time:
            return 0.0
        duration = self.end_time - self.start_time
        return self.total_requests / duration if duration > 0 else 0.0

    def add_response_time(self, response_time: float):
        """Add response time to metrics"""
        self.response_times.append(response_time)
        self.total_response_time += response_time
        self.min_response_time = min(self.min_response_time, response_time)
        self.max_response_time = max(self.max_response_time, response_time)

    def add_error(self, error: Exception, request_data: dict | None = None):
        """Add error to metrics"""
        self.failed_requests += 1
        self.errors.append(
            {
                "error": str(error),
                "type": type(error).__name__,
                "request_data": request_data,
                "timestamp": time.time(),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "average_response_time": self.average_response_time,
            "min_response_time": self.min_response_time
            if self.min_response_time != float("inf")
            else 0,
            "max_response_time": self.max_response_time,
            "throughput": self.throughput,
            "total_duration": (self.end_time - self.start_time)
            if self.start_time and self.end_time
            else 0,
            "errors": self.errors,
        }


class ChatBotLoadTester:
    """Load testing client for ChatBot SSE Server"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = None
        self.metrics = TestMetrics()

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def send_single_request(
        self, message: str, conversation_id: str | None = None
    ) -> dict[str, Any]:
        """Send a single chat request"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with statement.")

        start_time = time.time()
        self.metrics.total_requests += 1

        try:
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field("message", message)
            if conversation_id:
                data.add_field("conversation_id", conversation_id)

            # Send request
            async with self.session.post(
                f"{self.base_url}/chat", data=data
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")

                # Process SSE stream
                full_response = ""
                event_count = 0
                last_message = ""
                received_complete_event = False

                async for line in response.content:
                    if line:
                        line_str = line.decode("utf-8").strip()
                        if line_str.startswith("data: "):
                            try:
                                # 解析 data: event='message' data='{"type": "complete", ...}' 格式
                                data_part = line_str[6:]  # 去掉 "data: "

                                # 查找 JSON 部分
                                json_start = data_part.find("data='")
                                if json_start != -1:
                                    json_start += 6  # 跳过 'data=\''
                                    json_end = data_part.find("'", json_start)
                                    if json_end != -1:
                                        json_str = data_part[json_start:json_end]
                                        data = json.loads(json_str)
                                        event_count += 1

                                        if data.get("type") == "complete":
                                            last_message = data.get("content", "")
                                            received_complete_event = True
                                        elif data.get("type") == "completed":
                                            # 处理最终的 completed 事件
                                            last_message = data.get("content", "")
                                            received_complete_event = True

                                        full_response += data.get("content", "")
                            except (json.JSONDecodeError, ValueError):
                                # 解析失败时跳过这行
                                pass

                response_time = time.time() - start_time

                # 检查是否收到了完整的响应（必须包含complete事件）
                if event_count == 0 or not last_message:
                    # 没有收到SSE事件或没有收到complete事件，标记为失败
                    error_msg = f"Incomplete SSE response: {event_count} events, no complete event"
                    self.metrics.add_error(
                        Exception(error_msg),
                        {"message": message, "conversation_id": conversation_id},
                    )
                    return {
                        "success": False,
                        "response_time": response_time,
                        "error": error_msg,
                        "conversation_id": conversation_id,
                        "event_count": event_count,
                    }
                else:
                    # 收到完整响应，标记为成功
                    self.metrics.add_response_time(response_time)
                    self.metrics.successful_requests += 1

                return {
                    "success": True,
                    "response_time": response_time,
                    "event_count": event_count,
                    "conversation_id": conversation_id,
                    "message_length": len(full_response),
                    "last_message": last_message,
                    "received_complete_event": received_complete_event,
                }

        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.add_error(
                e, {"message": message, "conversation_id": conversation_id}
            )
            return {
                "success": False,
                "response_time": response_time,
                "error": str(e),
                "conversation_id": conversation_id,
            }

    async def run_concurrent_test(
        self,
        num_requests: int,
        concurrency: int,
        messages: list[str] | None = None,
        multi_turn: bool = False,
    ) -> dict[str, Any]:
        """Run concurrent load test"""
        self.metrics.start_time = time.time()

        if not messages:
            messages = [
                "Hello, how are you?",
                "What can you help me with?",
                "Tell me about artificial intelligence",
                "How does machine learning work?",
                "What are the benefits of Python?",
                "Explain the concept of async programming",
                "What is the difference between FastAPI and Flask?",
                "How do you optimize web application performance?",
                "What are microservices?",
                "Explain the concept of serverless computing",
            ]

        semaphore = asyncio.Semaphore(concurrency)
        conversation_ids: dict[int, str] = {}

        async def send_request(request_id: int):
            async with semaphore:
                message = messages[request_id % len(messages)]
                conversation_id = conversation_ids.get(request_id)

                result = await self.send_single_request(message, conversation_id)

                if result.get("success"):
                    # Extract conversation_id from response if available
                    if result.get("conversation_id") is None and multi_turn:
                        # For multi-turn, we need to track conversation IDs
                        conversation_ids[request_id] = str(
                            request_id
                        )  # Use request_id as conversation_id for now
                elif multi_turn:
                    conversation_ids[request_id] = None

                return result

        # Create progress bar
        with tqdm(total=num_requests, desc="Sending requests") as pbar:
            tasks = [send_request(i) for i in range(num_requests)]
            results = []
            for future in asyncio.as_completed(tasks):
                result = await future
                results.append(result)
                pbar.update(1)

        self.metrics.end_time = time.time()
        return {
            "results": results,
            "metrics": self.metrics.to_dict(),
        }

    async def run_ramp_up_test(
        self,
        max_concurrency: int,
        ramp_up_duration: int,
        duration: int,
        messages: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run ramp-up load test"""
        self.metrics.start_time = time.time()

        if not messages:
            messages = ["Test message for ramp-up test"]

        results = []
        active_tasks = set()
        start_time = time.time()

        async def worker():
            """Worker function for ramp-up test"""
            while time.time() - start_time < duration:
                message = messages[0]  # Use first message for simplicity
                result = await self.send_single_request(message)
                results.append(result)
                await asyncio.sleep(1)  # Small delay between requests

        # Ramp up workers
        for _i in range(max_concurrency):
            task = asyncio.create_task(worker())
            active_tasks.add(task)

            # Calculate delay between starting workers
            if ramp_up_duration > 0:
                delay = ramp_up_duration / max_concurrency
                await asyncio.sleep(delay)

        # Wait for test duration
        await asyncio.sleep(duration - ramp_up_duration)

        # Cancel remaining tasks
        for task in active_tasks:
            task.cancel()

        self.metrics.end_time = time.time()
        return {
            "results": results,
            "metrics": self.metrics.to_dict(),
        }

    async def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception:
            return False

    async def get_metrics(self) -> dict[str, Any]:
        """Get server metrics"""
        try:
            async with self.session.get(f"{self.base_url}/metrics") as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return {}


async def main():
    """Main function for running load tests"""
    import argparse

    parser = argparse.ArgumentParser(description="ChatBot SSE Server Load Testing")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--requests", type=int, default=100, help="Number of requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrency level")
    parser.add_argument(
        "--multi-turn", action="store_true", help="Enable multi-turn conversation"
    )
    parser.add_argument("--ramp-up", type=int, help="Ramp-up duration in seconds")
    parser.add_argument(
        "--duration", type=int, default=60, help="Test duration in seconds"
    )
    parser.add_argument("--output", help="Output file for results")

    args = parser.parse_args()

    print(f"Starting load test against {args.url}")
    print(f"Requests: {args.requests}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Multi-turn: {args.multi_turn}")

    async with ChatBotLoadTester(args.url) as tester:
        # Health check
        if not await tester.health_check():
            print("Error: Server is not responding")
            return

        print("Server is healthy")

        if args.ramp_up:
            # Run ramp-up test
            results = await tester.run_ramp_up_test(
                max_concurrency=args.concurrency,
                ramp_up_duration=args.ramp_up,
                duration=args.duration,
            )
        else:
            # Run concurrent test
            results = await tester.run_concurrent_test(
                num_requests=args.requests,
                concurrency=args.concurrency,
                multi_turn=args.multi_turn,
            )

        # Print results
        metrics = results["metrics"]
        print("\n=== Load Test Results ===")
        print(f"Total Requests: {metrics['total_requests']}")
        print(f"Successful Requests: {metrics['successful_requests']}")
        print(f"Failed Requests: {metrics['failed_requests']}")
        print(f"Success Rate: {metrics['success_rate']:.2f}%")
        print(f"Average Response Time: {metrics['average_response_time']:.3f}s")
        print(f"Min Response Time: {metrics['min_response_time']:.3f}s")
        print(f"Max Response Time: {metrics['max_response_time']:.3f}s")
        print(f"Throughput: {metrics['throughput']:.2f} requests/second")
        print(f"Total Duration: {metrics['total_duration']:.2f}s")

        if metrics["errors"]:
            print(f"\nErrors ({len(metrics['errors'])}):")
            for error in metrics["errors"][:5]:  # Show first 5 errors
                print(f"  - {error['type']}: {error['error']}")

        # Save results to file
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
