"""
Simple synchronous client for testing the ChatBot SSE Server
"""

import json
import time
from typing import Any

import httpx


class SimpleChatClient:
    """Simple synchronous client for testing"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def send_message(
        self, message: str, conversation_id: str | None = None
    ) -> dict[str, Any]:
        """Send a message and get response"""
        data = {
            "message": message,
        }
        if conversation_id:
            data["conversation_id"] = conversation_id

        response = self.client.post(
            f"{self.base_url}/chat",
            data=data,
            timeout=30.0,
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "content": response.text,
            }

        # Process SSE stream
        full_content = ""
        event_count = 0
        current_conversation_id = None

        for line in response.iter_lines():
            if line:  # Skip empty lines
                line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        event_count += 1

                        if data.get("type") == "connected":
                            current_conversation_id = data.get("conversation_id")
                        elif data.get("type") in ["partial_response", "complete"]:
                            content = data.get("content", "")
                            full_content += content

                    except json.JSONDecodeError:
                        continue

        return {
            "success": True,
            "conversation_id": current_conversation_id,
            "content": full_content,
            "event_count": event_count,
        }

    def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            response = self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def get_metrics(self) -> dict[str, Any]:
        """Get server metrics"""
        try:
            response = self.client.get(f"{self.base_url}/metrics")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {}


def run_simple_test():
    """Run a simple test"""
    client = SimpleChatClient()

    if not client.health_check():
        print("Server is not healthy")
        return

    print("Server is healthy")

    # Test messages
    messages = [
        "Hello, how are you?",
        "What can you help me with?",
        "Tell me about artificial intelligence",
    ]

    for i, message in enumerate(messages):
        print(f"\nMessage {i + 1}: {message}")

        start_time = time.time()
        result = client.send_message(message)
        end_time = time.time()

        if result["success"]:
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Events received: {result['event_count']}")
            print(f"Response: {result['content'][:100]}...")
            print(f"Conversation ID: {result['conversation_id']}")
        else:
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    run_simple_test()
