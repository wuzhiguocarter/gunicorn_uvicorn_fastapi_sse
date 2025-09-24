#!/usr/bin/env python3
"""
阶梯式压力测试脚本
逐步增加并发用户数，直到服务器达到性能极限
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Any

import aiohttp
import psutil

try:
    from tqdm import tqdm
except ImportError:
    print("⚠️ tqdm 未安装，正在安装...")
    os.system("uv pip install tqdm")
    from tqdm import tqdm

from src.load_test.client import ChatBotLoadTester


class SystemMonitor:
    """系统资源监控器"""

    def __init__(self):
        self.cpu_data = []
        self.memory_data = []
        self.start_time = time.time()

    def get_system_stats(self) -> dict[str, float]:
        """获取系统资源使用情况"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        return {
            "cpu_percent": cpu_percent,
            "cpu_idle": 100 - cpu_percent,
            "memory_percent": memory.percent,
            "memory_used": memory.used / (1024**3),  # GB
            "memory_total": memory.total / (1024**3),  # GB
            "timestamp": time.time() - self.start_time,
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
        self.report_dir = None

    async def health_check(self) -> bool:
        """检查服务器健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except:
            return False

    async def get_server_metrics(self) -> dict[str, Any]:
        """获取服务器指标"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/metrics") as response:
                    if response.status == 200:
                        return await response.json()
        except:
            pass
        return {}

    async def run_single_test_phase(
        self,
        concurrency: int,
        duration: int = 30,
        phase_name: str = "",
        phase_num: int = 1,
        total_phases: int = 1,
    ) -> dict[str, Any]:
        """运行单个测试阶段"""
        print(f"\n{'=' * 80}")
        print(f"🚀 第 {phase_num}/{total_phases} 阶段: {phase_name}")
        print(f"{'=' * 80}")
        print("📊 测试配置:")
        print(f"   • 并发用户数: {concurrency}")
        print(f"   • 测试时长: {duration}秒")
        print(f"   • 测试消息池: {len(self.test_messages)} 条")

        # 显示进度条
        print("\n⏳ 正在执行测试...")
        progress_bar = tqdm(
            total=duration,
            desc=f"🔄 {phase_name}",
            unit="s",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        )

        # 记录开始时的系统状态
        start_time = time.time()
        start_server_metrics = await self.get_server_metrics()
        start_system_stats = self.system_monitor.get_system_stats()

        # 运行负载测试
        async with ChatBotLoadTester(self.base_url) as tester:
            # 创建实时更新任务
            async def update_progress():
                elapsed = 0
                while elapsed < duration:
                    await asyncio.sleep(1)
                    elapsed = int(time.time() - start_time)
                    progress_bar.update(1)

                    # 每5秒显示一次系统状态
                    if elapsed % 5 == 0:
                        current_stats = self.system_monitor.get_system_stats()
                        progress_bar.set_postfix(
                            {
                                "CPU": f"{current_stats['cpu_percent']:.1f}%",
                                "MEM": f"{current_stats['memory_percent']:.1f}%",
                                "成功率": "计算中...",
                            }
                        )

            # 启动进度更新
            progress_task = asyncio.create_task(update_progress())

            try:
                # 运行压测
                results = await tester.run_ramp_up_test(
                    max_concurrency=concurrency,
                    ramp_up_duration=min(10, duration // 3),
                    duration=duration,
                    messages=self.test_messages,
                )
            finally:
                # 确保进度条完成
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
                progress_bar.close()

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
                "errors": metrics["errors"][:5]
                if metrics["errors"]
                else [],  # 只保留前5个错误
            }

            # 打印结果
            print("\n📊 测试结果:")
            print(f"   {'✅ 成功率':<15} {metrics['success_rate']:>6.1f}%")
            print(
                f"   {'⚡ 平均响应时间':<15} {metrics['average_response_time']:>6.3f}s"
            )
            print(f"   {'📈 吞吐量':<15} {metrics['throughput']:>6.2f} req/s")
            print(
                f"   {'💻 CPU使用率':<15} {start_system_stats['cpu_percent']:>5.1f}% → {end_system_stats['cpu_percent']:>5.1f}%"
            )
            print(
                f"   {'🧠 CPU空闲率':<15} {start_system_stats['cpu_idle']:>5.1f}% → {end_system_stats['cpu_idle']:>5.1f}%"
            )
            print(
                f"   {'🗄️ 内存使用率':<15} {start_system_stats['memory_percent']:>5.1f}% → {end_system_stats['memory_percent']:>5.1f}%"
            )
            print(f"   {'📝 总请求数':<15} {metrics['total_requests']:>6}")
            print(f"   {'✅ 成功请求数':<15} {metrics['successful_requests']:>6}")
            print(f"   {'❌ 失败请求数':<15} {metrics['failed_requests']:>6}")

            if metrics["failed_requests"] > 0:
                print("\n⚠️ 主要错误:")
                for i, error in enumerate(metrics["errors"][:3], 1):
                    error_msg = (
                        error.get("error", str(error))
                        if isinstance(error, dict)
                        else str(error)
                    )
                    print(f"   {i}. {error_msg[:100]}...")

            return test_results

    def should_stop_test(
        self, current_result: dict[str, Any], previous_result: dict[str, Any] = None
    ) -> bool:
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
            warnings.append(f"⚠️ 错误率过高 ({100 - success_rate:.1f}%)")

        if (
            previous_result
            and avg_response_time > previous_result["avg_response_time"] * 2
        ):
            warnings.append(
                f"⚠️ 响应时间大幅增加 ({avg_response_time:.3f}s vs {previous_result['avg_response_time']:.3f}s)"
            )

        if memory_percent > 90:
            warnings.append(f"⚠️ 内存使用率过高 ({memory_percent:.1f}%)")

        if warnings:
            print("\n⚠️ 性能警告:")
            for warning in warnings:
                print(f"   {warning}")
            return True  # 标记达到性能极限，但不停止测试

        return False

    async def run_ramp_up_test(self):
        """运行完整的阶梯式负载测试"""
        print("🔥" + "=" * 79)
        print("🔥                    阶梯式压力测试开始")
        print("🔥" + "=" * 79)
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 测试目标: {self.base_url}")
        print("📊 测试阶段: 共9个阶段，逐步增加负载")
        print("🔥" + "=" * 79)

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
            while hasattr(self, "_monitoring") and self._monitoring:
                self.system_monitor.record_stats()
                time.sleep(1)

        self._monitoring = True
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()

        try:
            previous_result = None
            performance_limit_reached = False

            # 显示整体进度条
            total_phases = len(test_phases)
            overall_progress = tqdm(
                total=total_phases,
                desc="📊 整体进度",
                unit="阶段",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
            )

            for i, phase in enumerate(test_phases):
                # 更新整体进度
                overall_progress.update(1)
                overall_progress.set_description(f"📊 {phase['name']}")

                # 运行测试阶段
                result = await self.run_single_test_phase(
                    concurrency=phase["concurrency"],
                    duration=phase["duration"],
                    phase_name=phase["name"],
                    phase_num=i + 1,
                    total_phases=total_phases,
                )

                self.results.append(result)

                # 检查是否达到性能极限（仅警告，不停止）
                if self.should_stop_test(result, previous_result):
                    if not performance_limit_reached:
                        print(f"\n🎯 首次达到性能极限标记点: {phase['name']}")
                        performance_limit_reached = True

                # 如果是最后一个阶段，也停止
                if i == len(test_phases) - 1:
                    print("\n🏁 已完成所有测试阶段")
                    break

                # 阶段间休息
                if i < len(test_phases) - 1:
                    print("\n⏳ 阶段间休息 10 秒...")
                    for countdown in range(10, 0, -1):
                        sys.stdout.write(f"\r⏳ 准备下一阶段: {countdown:2d} 秒")
                        sys.stdout.flush()
                        await asyncio.sleep(1)
                    sys.stdout.write("\r" + " " * 30 + "\r")
                    sys.stdout.flush()

                previous_result = result

            overall_progress.close()

        finally:
            self._monitoring = False
            if monitor_thread.is_alive():
                monitor_thread.join(timeout=2)

        return self.results

    def save_results(self, filename: str = "ramp_up_test_results.json"):
        """保存测试结果"""
        # 创建报告目录
        self._create_report_directory()

        # 构建完整文件路径
        full_path = os.path.join(self.report_dir, filename)

        results_data = {
            "test_info": {
                "base_url": self.base_url,
                "test_time": datetime.now().isoformat(),
                "total_phases": len(self.results),
            },
            "results": self.results,
            "system_monitoring": {
                "cpu_data": self.system_monitor.cpu_data,
                "memory_data": self.system_monitor.memory_data,
            },
        }

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 测试结果已保存到: {full_path}")

    def _create_report_directory(self):
        """创建带时间戳的报告目录"""
        if self.report_dir is None:
            timestamp = datetime.now().strftime("%y%m%dT%H%M")
            self.report_dir = os.path.join("reports", timestamp)
            os.makedirs(self.report_dir, exist_ok=True)
            print(f"📁 创建报告目录: {self.report_dir}")

    def generate_report(self):
        """生成测试报告"""
        if not self.results:
            print("没有测试结果")
            return

        # 创建报告目录
        self._create_report_directory()

        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"ramp_up_test_report_{timestamp}.md"
        full_path = os.path.join(self.report_dir, report_filename)

        # 构建报告内容
        report_content = self._build_report_content()

        # 保存报告到文件
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        # 打印报告到终端
        self._print_report_to_terminal(report_content)

        print(f"\n💾 测试报告已保存到: {full_path}")

    def _build_report_content(self) -> str:
        """构建 markdown 格式的报告内容"""
        if not self.results:
            return "# 阶梯式压力测试报告\n\n没有测试结果"

        report_lines = []
        report_lines.append("# 📊 阶梯式压力测试报告")
        report_lines.append(
            f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append(f"**测试目标**: {self.base_url}")
        report_lines.append("")

        # 分析所有阶段的性能拐点
        performance_knees = []
        for i, result in enumerate(self.results):
            issues = []
            if result["success_rate"] < 95:
                issues.append(f"错误率: {100 - result['success_rate']:.1f}%")
            if result["end_cpu_idle"] < 30:
                issues.append(f"CPU空闲率: {result['end_cpu_idle']:.1f}%")
            if result["end_memory_percent"] > 90:
                issues.append(f"内存使用率: {result['end_memory_percent']:.1f}%")

            if issues:
                performance_knees.append(
                    {
                        "phase": i + 1,
                        "concurrency": result["concurrency"],
                        "throughput": result["throughput"],
                        "success_rate": result["success_rate"],
                        "issues": issues,
                    }
                )

        report_lines.append("## 🎯 性能拐点分析")
        if performance_knees:
            report_lines.append(f"发现 {len(performance_knees)} 个性能拐点:")
            report_lines.append("")
            for knee in performance_knees:
                report_lines.append(
                    f"### 第 {knee['phase']} 阶段 ({knee['concurrency']} 并发用户)"
                )
                report_lines.append(f"- **吞吐量**: {knee['throughput']:.2f} req/s")
                report_lines.append(f"- **成功率**: {knee['success_rate']:.1f}%")
                report_lines.append(f"- **问题**: {', '.join(knee['issues'])}")
                report_lines.append("")
        else:
            report_lines.append("🎉 在测试范围内未发现明显的性能拐点")
        report_lines.append("")

        # 找到最佳性能点（综合考虑吞吐量和成功率）
        best_throughput = max(self.results, key=lambda x: x["throughput"])
        best_success_rate = max(self.results, key=lambda x: x["success_rate"])

        report_lines.append("## 🏆 最佳性能点")
        report_lines.append(
            f"- **最高吞吐量**: {best_throughput['concurrency']} 并发用户, {best_throughput['throughput']:.2f} req/s"
        )
        report_lines.append(
            f"- **最高成功率**: {best_success_rate['concurrency']} 并发用户, {best_success_rate['success_rate']:.1f}%"
        )
        report_lines.append("")

        # 性能趋势分析
        report_lines.append("## 📈 性能趋势分析")
        report_lines.append("")
        report_lines.append(
            "| 并发用户 | 成功率 | 吞吐量 (req/s) | 响应时间 (s) | 内存使用率 |"
        )
        report_lines.append(
            "|----------|--------|----------------|---------------|------------|"
        )
        for result in self.results:
            report_lines.append(
                f"| {result['concurrency']} | {result['success_rate']:.1f}% | {result['throughput']:.2f} | {result['avg_response_time']:.3f} | {result['end_memory_percent']:.1f}% |"
            )
        report_lines.append("")

        # 总结
        total_requests = sum(r["total_requests"] for r in self.results)
        total_errors = sum(r["failed_requests"] for r in self.results)
        overall_success_rate = (total_requests - total_errors) / total_requests * 100
        avg_throughput = sum(r["throughput"] for r in self.results) / len(self.results)

        report_lines.append("## 📊 测试总结")
        report_lines.append(f"- **总请求数**: {total_requests}")
        report_lines.append(f"- **总错误数**: {total_errors}")
        report_lines.append(f"- **整体成功率**: {overall_success_rate:.2f}%")
        report_lines.append(f"- **平均吞吐量**: {avg_throughput:.2f} req/s")
        report_lines.append(f"- **测试阶段数**: {len(self.results)}")
        report_lines.append("")

        # 综合评估
        report_lines.append("## 🔍 综合性能评估")
        if overall_success_rate >= 95:
            report_lines.append("✅ 整体成功率良好")
        else:
            report_lines.append(f"⚠️ 整体成功率偏低: {overall_success_rate:.1f}%")

        # 找出性能最稳定的阶段
        stable_phases = [r for r in self.results if r["success_rate"] >= 95]
        if stable_phases:
            max_stable_concurrency = max(stable_phases, key=lambda x: x["concurrency"])
            report_lines.append(
                f"✅ 系统在 {max_stable_concurrency['concurrency']} 并发用户内表现稳定"
            )
        else:
            report_lines.append("❌ 系统在所有测试阶段都存在性能问题")
        report_lines.append("")

        # 详细结果
        report_lines.append("## 📋 详细测试结果")
        report_lines.append("")
        for i, result in enumerate(self.results):
            report_lines.append(f"### 阶段 {i + 1}: {result['phase']}")
            report_lines.append(f"- **并发用户数**: {result['concurrency']}")
            report_lines.append(f"- **测试时长**: {result['duration']} 秒")
            report_lines.append(f"- **总请求数**: {result['total_requests']}")
            report_lines.append(f"- **成功请求数**: {result['successful_requests']}")
            report_lines.append(f"- **失败请求数**: {result['failed_requests']}")
            report_lines.append(f"- **成功率**: {result['success_rate']:.1f}%")
            report_lines.append(
                f"- **平均响应时间**: {result['avg_response_time']:.3f}s"
            )
            report_lines.append(
                f"- **最小响应时间**: {result['min_response_time']:.3f}s"
            )
            report_lines.append(
                f"- **最大响应时间**: {result['max_response_time']:.3f}s"
            )
            report_lines.append(f"- **吞吐量**: {result['throughput']:.2f} req/s")
            report_lines.append(
                f"- **CPU使用率**: {result['start_cpu_percent']:.1f}% → {result['end_cpu_percent']:.1f}%"
            )
            report_lines.append(
                f"- **CPU空闲率**: {result['start_cpu_idle']:.1f}% → {result['end_cpu_idle']:.1f}%"
            )
            report_lines.append(
                f"- **内存使用率**: {result['start_memory_percent']:.1f}% → {result['end_memory_percent']:.1f}%"
            )

            if result["errors"]:
                report_lines.append("- **主要错误**:")
                for error in result["errors"]:
                    report_lines.append(f"  - {error}")
            report_lines.append("")

        return "\n".join(report_lines)

    def _print_report_to_terminal(self, report_content: str):
        """打印报告到终端（去除markdown格式）"""
        print("\n" + "=" * 60)
        print("📊 阶梯式压力测试报告")
        print("=" * 60)

        # 简化处理，只打印关键内容
        lines = report_content.split("\n")
        skip_next = False
        for line in lines:
            # 跳过markdown标题和表格格式
            if line.startswith("#") or line.startswith("|") or line.startswith("-"):
                if line.startswith("## 📈 性能趋势分析"):
                    print("\n📈 性能趋势分析:")
                    print("   并发用户 | 成功率 | 吞吐量 | 响应时间 | 内存使用")
                    print("   " + "-" * 60)
                    skip_next = True
                elif line.startswith("## 📊 测试总结"):
                    print("\n📊 测试总结:")
                elif line.startswith("## 🔍 综合性能评估"):
                    print("\n🔍 综合性能评估:")
                elif line.startswith("- **总请求数**"):
                    print(f"   • {line[3:]}")
                elif line.startswith("- **总错误数**"):
                    print(f"   • {line[3:]}")
                elif line.startswith("- **整体成功率**"):
                    print(f"   • {line[3:]}")
                elif line.startswith("- **平均吞吐量**"):
                    print(f"   • {line[3:]}")
                elif line.startswith("- **测试阶段数**"):
                    print(f"   • {line[3:]}")
                elif (
                    line.startswith("✅")
                    or line.startswith("⚠️")
                    or line.startswith("❌")
                ):
                    print(f"   {line}")
            elif skip_next:
                # 处理表格行
                if line.startswith("|"):
                    parts = line.split("|")[1:-1]
                    if len(parts) >= 5:
                        concurrency = parts[0].strip()
                        success_rate = parts[1].strip()
                        throughput = parts[2].strip()
                        response_time = parts[3].strip()
                        memory = parts[4].strip()
                        print(
                            f"   {concurrency:>8} | {success_rate:>7} | {throughput:>7} | {response_time:>11} | {memory:>10}"
                        )
                else:
                    skip_next = False
            elif line.startswith("### 阶段"):
                # 跳过详细结果
                pass
            elif line.startswith("## 🎯 性能拐点分析"):
                # 处理性能拐点
                print("🎯 发现性能拐点:")
            elif line.startswith("### 第") and "阶段" in line:
                # 处理具体的性能拐点
                phase_info = line.split("第")[1].split("阶段")
                phase_num = phase_info[0].strip()
                concurrency = phase_info[1].split("(")[1].split("并发用户")[0].strip()
                print(f"   第 {phase_num} 阶段 ({concurrency} 并发用户):")
            elif line.startswith("- **吞吐量**:") and "性能拐点" in report_content:
                print(f"     • {line[3:]}")
            elif line.startswith("- **成功率**:") and "性能拐点" in report_content:
                print(f"     • {line[3:]}")
            elif line.startswith("- **问题**:") and "性能拐点" in report_content:
                print(f"     • {line[3:]}")
            elif line.startswith("🎉 在测试范围内未发现明显的性能拐点"):
                print("🎉 在测试范围内未发现明显的性能拐点")
            elif line.startswith("## 🏆 最佳性能点"):
                print("\n🏆 最佳性能点:")
            elif (
                line.startswith("- **最高吞吐量**:") and "最佳性能点" in report_content
            ):
                print(f"   • {line[3:]}")
            elif (
                line.startswith("- **最高成功率**:") and "最佳性能点" in report_content
            ):
                print(f"   • {line[3:]}")


async def main(args):
    """主函数"""
    print("🚀" + "=" * 79)
    print("🚀            ChatBot SSE 服务器阶梯式压力测试")
    print("🚀" + "=" * 79)
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀" + "=" * 79)

    # 创建测试器
    base_url = args.url if args.url else "http://localhost:8000"
    tester = RampUpLoadTester(base_url=base_url)

    # 检查服务器状态
    print("🔍 检查服务器状态...")
    health_check_progress = tqdm(
        total=10, desc="🔍 服务器健康检查", bar_format="{desc}", leave=False
    )

    for _ in range(10):
        if await tester.health_check():
            health_check_progress.update(10)
            health_check_progress.close()
            print("✅ 服务器运行正常")
            break
        await asyncio.sleep(0.5)
        health_check_progress.update(1)
    else:
        health_check_progress.close()
        print("❌ 服务器不可用，请检查服务器是否正在运行")
        return

    print("\n🔧 准备测试环境...")
    print(f"   📊 测试目标: {tester.base_url}")
    print(f"   📝 测试消息池: {len(tester.test_messages)} 条")
    print("   📁 报告输出: 时间戳目录")

    # 处理用户交互
    if args.no_prompt:
        print("\n⚡ 跳过交互提示，直接开始测试...")
    else:
        try:
            input("\n⚡ 按回车键开始测试...")
        except (EOFError, KeyboardInterrupt):
            print("\n⚡ 检测到非交互环境，直接开始测试...")

    # 运行测试
    await tester.run_ramp_up_test()

    # 保存结果
    print("\n💾 保存测试结果...")
    tester.save_results()

    # 生成报告
    print("\n📊 生成测试报告...")
    tester.generate_report()

    print("\n🎉" + "=" * 79)
    print("🎉                    测试完成！")
    print("🎉" + "=" * 79)
    print(f"📁 测试报告已保存到: {tester.report_dir}")
    print("🎉" + "=" * 79)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="ChatBot SSE 服务器阶梯式压力测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python ramp_up_test.py                    # 交互模式运行
  python ramp_up_test.py --no-prompt        # 跳过交互提示
  python ramp_up_test.py --url http://localhost:8080  # 指定服务器URL
  python ramp_up_test.py --no-prompt --url http://localhost:8080  # 非交互模式
        """,
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="跳过交互提示，直接开始测试（适用于CI/CD环境）",
    )
    parser.add_argument(
        "--url", type=str, help="指定服务器URL（默认：http://localhost:8000）"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(main(args))
