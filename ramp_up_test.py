#!/usr/bin/env python3
"""
阶梯式压力测试脚本
逐步增加并发用户数，直到服务器达到性能极限
"""

import asyncio
import json
import time
import psutil
from datetime import datetime
from typing import Dict, Any
import aiohttp

from src.load_test.client import ChatBotLoadTester


class SystemMonitor:
    """系统资源监控器"""

    def __init__(self):
        self.cpu_data = []
        self.memory_data = []
        self.start_time = time.time()

    def get_system_stats(self) -> Dict[str, float]:
        """获取系统资源使用情况"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        return {
            "cpu_percent": cpu_percent,
            "cpu_idle": 100 - cpu_percent,
            "memory_percent": memory.percent,
            "memory_used": memory.used / (1024**3),  # GB
            "memory_total": memory.total / (1024**3),  # GB
            "timestamp": time.time() - self.start_time
        }

    def record_stats(self):
        """记录系统状态"""
        stats = self.get_system_stats()
        self.cpu_data.append(stats)
        self.memory_data.append(stats)


class RampUpLoadTester:
    """阶梯式负载测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.system_monitor = SystemMonitor()
        self.test_messages = [
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

    async def health_check(self) -> bool:
        """检查服务器健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except:
            return False

    async def get_server_metrics(self) -> Dict[str, Any]:
        """获取服务器指标"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/metrics") as response:
                    if response.status == 200:
                        return await response.json()
        except:
            pass
        return {}

    async def run_single_test_phase(self,
                                  concurrency: int,
                                  duration: int = 30,
                                  phase_name: str = "") -> Dict[str, Any]:
        """运行单个测试阶段"""
        print(f"\n🚀 开始测试阶段: {phase_name}")
        print(f"   并发用户数: {concurrency}")
        print(f"   测试时长: {duration}秒")

        # 记录开始时的系统状态
        start_time = time.time()
        start_server_metrics = await self.get_server_metrics()
        start_system_stats = self.system_monitor.get_system_stats()

        # 运行负载测试
        async with ChatBotLoadTester(self.base_url) as tester:
            # 运行压测
            results = await tester.run_ramp_up_test(
                max_concurrency=concurrency,
                ramp_up_duration=min(10, duration // 3),
                duration=duration,
                messages=self.test_messages
            )

            # 记录结束时的系统状态
            end_time = time.time()
            end_server_metrics = await self.get_server_metrics()
            end_system_stats = self.system_monitor.get_system_stats()

            # 计算性能指标
            metrics = results["metrics"]
            test_results = {
                "phase": phase_name,
                "concurrency": concurrency,
                "duration": duration,
                "start_time": start_time,
                "end_time": end_time,

                # 请求指标
                "total_requests": metrics["total_requests"],
                "successful_requests": metrics["successful_requests"],
                "failed_requests": metrics["failed_requests"],
                "success_rate": metrics["success_rate"],

                # 性能指标
                "avg_response_time": metrics["average_response_time"],
                "min_response_time": metrics["min_response_time"],
                "max_response_time": metrics["max_response_time"],
                "throughput": metrics["throughput"],

                # 系统资源
                "start_cpu_percent": start_system_stats["cpu_percent"],
                "start_cpu_idle": start_system_stats["cpu_idle"],
                "start_memory_percent": start_system_stats["memory_percent"],
                "end_cpu_percent": end_system_stats["cpu_percent"],
                "end_cpu_idle": end_system_stats["cpu_idle"],
                "end_memory_percent": end_system_stats["memory_percent"],

                # 服务器指标
                "start_total_requests": start_server_metrics.get("total_requests", 0),
                "end_total_requests": end_server_metrics.get("total_requests", 0),

                # 错误信息
                "errors": metrics["errors"][:5] if metrics["errors"] else []  # 只保留前5个错误
            }

            # 打印结果
            print(f"   📊 测试结果:")
            print(f"      ✓ 成功率: {metrics['success_rate']:.1f}%")
            print(f"      ✓ 平均响应时间: {metrics['average_response_time']:.3f}s")
            print(f"      ✓ 吞吐量: {metrics['throughput']:.2f} req/s")
            print(f"      ✓ CPU使用率: {start_system_stats['cpu_percent']:.1f}% → {end_system_stats['cpu_percent']:.1f}%")
            print(f"      ✓ CPU空闲率: {start_system_stats['cpu_idle']:.1f}% → {end_system_stats['cpu_idle']:.1f}%")
            print(f"      ✓ 内存使用率: {start_system_stats['memory_percent']:.1f}% → {end_system_stats['memory_percent']:.1f}%")

            if metrics["failed_requests"] > 0:
                print(f"      ❌ 失败请求数: {metrics['failed_requests']}")

            return test_results

    def should_stop_test(self, current_result: Dict[str, Any], previous_result: Dict[str, Any] = None) -> bool:
        """判断是否应该停止测试 - 现在仅用于警告，不停止测试"""
        # 停止条件：
        # 1. CPU空闲率低于30%
        # 2. 错误率超过5%
        # 3. 响应时间大幅增加（超过前一个阶段的2倍）
        # 4. 内存使用率超过90%

        end_cpu_idle = current_result["end_cpu_idle"]
        success_rate = current_result["success_rate"]
        avg_response_time = current_result["avg_response_time"]
        memory_percent = current_result["end_memory_percent"]

        warnings = []

        if end_cpu_idle < 30:
            warnings.append(f"⚠️ CPU空闲率过低 ({end_cpu_idle:.1f}%)")

        if success_rate < 95:
            warnings.append(f"⚠️ 错误率过高 ({100-success_rate:.1f}%)")

        if previous_result and avg_response_time > previous_result["avg_response_time"] * 2:
            warnings.append(f"⚠️ 响应时间大幅增加 ({avg_response_time:.3f}s vs {previous_result['avg_response_time']:.3f}s)")

        if memory_percent > 90:
            warnings.append(f"⚠️ 内存使用率过高 ({memory_percent:.1f}%)")

        if warnings:
            print(f"\n⚠️ 性能警告:")
            for warning in warnings:
                print(f"   {warning}")
            return True  # 标记达到性能极限，但不停止测试

        return False

    async def run_ramp_up_test(self):
        """运行完整的阶梯式负载测试"""
        print("🔥 开始阶梯式压力测试")
        print("=" * 60)

        # 测试阶段配置
        test_phases = [
            {"concurrency": 10, "duration": 20, "name": "低负载测试"},
            {"concurrency": 20, "duration": 20, "name": "中等负载测试"},
            {"concurrency": 30, "duration": 20, "name": "高负载测试"},
            {"concurrency": 40, "duration": 20, "name": "高负载测试"},
            {"concurrency": 50, "duration": 20, "name": "极高负载测试"},
            {"concurrency": 75, "duration": 20, "name": "极限负载测试"},
            {"concurrency": 100, "duration": 20, "name": "超极限测试"},
            {"concurrency": 150, "duration": 20, "name": "崩溃测试"},
            {"concurrency": 200, "duration": 20, "name": "压力测试"},
        ]

        # 启动系统监控
        import threading
        def monitor_system():
            while hasattr(self, '_monitoring') and self._monitoring:
                self.system_monitor.record_stats()
                time.sleep(1)

        self._monitoring = True
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()

        try:
            previous_result = None
            performance_limit_reached = False

            for i, phase in enumerate(test_phases):
                # 运行测试阶段
                result = await self.run_single_test_phase(
                    concurrency=phase["concurrency"],
                    duration=phase["duration"],
                    phase_name=phase["name"]
                )

                self.results.append(result)

                # 检查是否达到性能极限（仅警告，不停止）
                if self.should_stop_test(result, previous_result):
                    if not performance_limit_reached:
                        print(f"\n🎯 首次达到性能极限标记点: {phase['name']}")
                        performance_limit_reached = True

                # 如果是最后一个阶段，也停止
                if i == len(test_phases) - 1:
                    print(f"\n🏁 已完成所有测试阶段")
                    break

                # 阶段间休息
                print(f"   ⏳ 阶段间休息 10 秒...")
                await asyncio.sleep(10)

                previous_result = result

        finally:
            self._monitoring = False
            if monitor_thread.is_alive():
                monitor_thread.join(timeout=2)

        return self.results

    def save_results(self, filename: str = "ramp_up_test_results.json"):
        """保存测试结果"""
        results_data = {
            "test_info": {
                "base_url": self.base_url,
                "test_time": datetime.now().isoformat(),
                "total_phases": len(self.results)
            },
            "results": self.results,
            "system_monitoring": {
                "cpu_data": self.system_monitor.cpu_data,
                "memory_data": self.system_monitor.memory_data
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 测试结果已保存到: {filename}")

    def generate_report(self):
        """生成测试报告"""
        if not self.results:
            print("没有测试结果")
            return

        print("\n" + "=" * 60)
        print("📊 阶梯式压力测试报告")
        print("=" * 60)

        # 分析所有阶段的性能拐点
        performance_knees = []
        for i, result in enumerate(self.results):
            issues = []
            if result["success_rate"] < 95:
                issues.append(f"错误率: {100-result['success_rate']:.1f}%")
            if result["end_cpu_idle"] < 30:
                issues.append(f"CPU空闲率: {result['end_cpu_idle']:.1f}%")
            if result["end_memory_percent"] > 90:
                issues.append(f"内存使用率: {result['end_memory_percent']:.1f}%")

            if issues:
                performance_knees.append({
                    "phase": i + 1,
                    "concurrency": result["concurrency"],
                    "throughput": result["throughput"],
                    "success_rate": result["success_rate"],
                    "issues": issues
                })

        if performance_knees:
            print(f"🎯 发现 {len(performance_knees)} 个性能拐点:")
            for knee in performance_knees:
                print(f"   第 {knee['phase']} 阶段 ({knee['concurrency']} 并发用户):")
                print(f"     • 吞吐量: {knee['throughput']:.2f} req/s")
                print(f"     • 成功率: {knee['success_rate']:.1f}%")
                print(f"     • 问题: {', '.join(knee['issues'])}")
        else:
            print("🎉 在测试范围内未发现明显的性能拐点")

        # 找到最佳性能点（综合考虑吞吐量和成功率）
        best_throughput = max(self.results, key=lambda x: x["throughput"])
        best_success_rate = max(self.results, key=lambda x: x["success_rate"])

        print(f"\n🏆 最佳性能点:")
        print(f"   • 最高吞吐量: {best_throughput['concurrency']} 并发用户, {best_throughput['throughput']:.2f} req/s")
        print(f"   • 最高成功率: {best_success_rate['concurrency']} 并发用户, {best_success_rate['success_rate']:.1f}%")

        # 性能趋势分析
        print(f"\n📈 性能趋势分析:")
        print("   并发用户 | 成功率 | 吞吐量 | 响应时间 | 内存使用")
        print("   " + "-" * 60)
        for result in self.results:
            print(f"   {result['concurrency']:8d} | {result['success_rate']:5.1f}% | {result['throughput']:6.2f} | {result['avg_response_time']:7.3f}s | {result['end_memory_percent']:7.1f}%")

        # 总结
        total_requests = sum(r["total_requests"] for r in self.results)
        total_errors = sum(r["failed_requests"] for r in self.results)
        overall_success_rate = (total_requests - total_errors) / total_requests * 100
        avg_throughput = sum(r["throughput"] for r in self.results) / len(self.results)

        print(f"\n📊 测试总结:")
        print(f"   • 总请求数: {total_requests}")
        print(f"   • 总错误数: {total_errors}")
        print(f"   • 整体成功率: {overall_success_rate:.2f}%")
        print(f"   • 平均吞吐量: {avg_throughput:.2f} req/s")
        print(f"   • 测试阶段数: {len(self.results)}")

        # 综合评估
        print(f"\n🔍 综合性能评估:")
        if overall_success_rate >= 95:
            print("   ✅ 整体成功率良好")
        else:
            print(f"   ⚠️ 整体成功率偏低: {overall_success_rate:.1f}%")

        # 找出性能最稳定的阶段
        stable_phases = [r for r in self.results if r["success_rate"] >= 95]
        if stable_phases:
            max_stable_concurrency = max(stable_phases, key=lambda x: x["concurrency"])
            print(f"   ✅ 系统在 {max_stable_concurrency['concurrency']} 并发用户内表现稳定")
        else:
            print("   ❌ 系统在所有测试阶段都存在性能问题")


async def main():
    """主函数"""
    print("🔥 ChatBot SSE 服务器阶梯式压力测试")
    print("=" * 60)

    # 创建测试器
    tester = RampUpLoadTester(base_url="http://localhost:8000")

    # 检查服务器状态
    print("🔍 检查服务器状态...")
    if not await tester.health_check():
        print("❌ 服务器不可用，请检查服务器是否正在运行")
        return

    print("✅ 服务器运行正常")

    # 运行测试
    results = await tester.run_ramp_up_test()

    # 保存结果
    tester.save_results()

    # 生成报告
    tester.generate_report()


if __name__ == "__main__":
    asyncio.run(main())