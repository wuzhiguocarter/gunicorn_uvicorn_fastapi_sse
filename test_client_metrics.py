#!/usr/bin/env python3
"""
测试脚本验证load test client的失败请求检测是否正确工作
"""

import asyncio
import json
import time
from src.load_test.client import ChatBotLoadTester

async def test_client_metrics():
    """测试客户端指标收集的正确性"""
    print("🧪 测试Load Test Client的指标收集...")

    async with ChatBotLoadTester("http://localhost:8000") as tester:
        # 发送几个测试请求
        messages = [
            "Hello, how are you?",
            "What can you help me with?",
            "Tell me about artificial intelligence"
        ]

        print(f"📤 发送 {len(messages)} 个测试请求...")

        results = []
        for i, message in enumerate(messages):
            print(f"   请求 {i+1}: {message[:30]}...")
            result = await tester.send_single_request(message)
            results.append(result)

            # 等待一下避免过快请求
            await asyncio.sleep(0.5)

        # 打印详细结果
        print(f"\n📊 测试结果:")
        print(f"   {'编号':<5} {'成功':<6} {'事件数':<8} {'响应时间':<12} {'完整事件':<8}")
        print(f"   {'-'*45}")

        for i, result in enumerate(results):
            success = "✅" if result.get('success', False) else "❌"
            event_count = result.get('event_count', 0)
            response_time = f"{result.get('response_time', 0):.3f}s"
            complete = "✅" if result.get('received_complete_event', False) else "❌"
            print(f"   {i+1:<5} {success:<6} {event_count:<8} {response_time:<12} {complete:<8}")

        # 打印指标汇总
        metrics = tester.metrics
        print(f"\n📈 指标汇总:")
        print(f"   总请求数: {metrics.total_requests}")
        print(f"   成功请求数: {metrics.successful_requests}")
        print(f"   失败请求数: {metrics.failed_requests}")
        print(f"   计算的成功率: {metrics.success_rate:.1f}%")
        print(f"   验证成功率: {(metrics.successful_requests / metrics.total_requests * 100):.1f}%")

        # 验证数据一致性
        calculated_failed = metrics.total_requests - metrics.successful_requests
        if calculated_failed == metrics.failed_requests:
            print(f"   ✅ 数据一致性检查通过")
        else:
            print(f"   ❌ 数据不一致: calculated_failed={calculated_failed}, metrics.failed_requests={metrics.failed_requests}")

        # 显示错误详情
        if metrics.errors:
            print(f"\n❌ 错误详情:")
            for i, error in enumerate(metrics.errors, 1):
                print(f"   {i}. {error.get('error', 'Unknown error')}")
        else:
            print(f"\n✅ 没有检测到错误")

        return metrics

if __name__ == "__main__":
    asyncio.run(test_client_metrics())