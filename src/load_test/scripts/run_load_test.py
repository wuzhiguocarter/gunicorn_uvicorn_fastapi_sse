#!/usr/bin/env python3
"""
Run load tests for the ChatBot SSE Server
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.load_test.client import ChatBotLoadTester


def main():
    parser = argparse.ArgumentParser(
        description="Run load tests for ChatBot SSE Server"
    )
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
    parser.add_argument("--simple", action="store_true", help="Run simple test")

    args = parser.parse_args()

    if args.simple:
        # Run simple test
        from src.load_test.simple_client import run_simple_test

        run_simple_test()
        return

    print(f"Starting load test against {args.url}")
    print(f"Requests: {args.requests}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Multi-turn: {args.multi_turn}")

    async def run_test():
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

    asyncio.run(run_test())


if __name__ == "__main__":
    main()
