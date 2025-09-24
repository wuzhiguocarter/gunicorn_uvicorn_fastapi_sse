#!/usr/bin/env python3
"""
快速查看代码覆盖率报告的脚本
"""

import os
import subprocess
import sys
from pathlib import Path


def view_coverage():
    """查看覆盖率报告"""
    print("🔍 ChatBot SSE 服务器代码覆盖率")
    print("=" * 50)

    # 检查是否存在htmlcov目录
    htmlcov_dir = Path("htmlcov")
    if not htmlcov_dir.exists():
        print("❌ 未找到覆盖率报告，正在生成...")
        result = subprocess.run(
            [
                "uv",
                "run",
                "pytest",
                "--cov=src/app",
                "--cov-report=html",
                "--cov-report=term-missing",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ 生成覆盖率报告失败: {result.stderr}")
            return False

    # 读取覆盖率统计
    try:
        with open("htmlcov/status.json") as f:
            import json

            status = json.load(f)

        # 计算总体统计
        total_statements = sum(
            metrics["index"]["nums"]["n_statements"]
            for metrics in status["files"].values()
        )
        total_missing = sum(
            metrics["index"]["nums"]["n_missing"]
            for metrics in status["files"].values()
        )
        total_covered = total_statements - total_missing
        total_coverage = (
            (total_covered / total_statements) * 100 if total_statements > 0 else 0
        )

        print(f"📊 总体覆盖率: {total_coverage:.1f}%")
        print(f"📝 总行数: {total_statements}")
        print(f"✅ 已覆盖: {total_covered}")
        print(f"❌ 未覆盖: {total_missing}")
        print()

        # 显示各文件覆盖率
        print("📁 各文件覆盖率:")
        print("-" * 30)
        for _file_id, metrics in status["files"].items():
            file_info = metrics["index"]
            statements = file_info["nums"]["n_statements"]
            missing = file_info["nums"]["n_missing"]
            covered = statements - missing
            coverage = (covered / statements) * 100 if statements > 0 else 0

            # 从文件ID中提取文件名
            filename = file_info["file"].replace("src/app/", "")

            if coverage == 100.0:
                status_icon = "✅"
            elif coverage >= 90.0:
                status_icon = "⚠️"
            else:
                status_icon = "❌"

            print(f"{status_icon} {filename}: {coverage:.1f}% (缺失 {missing} 行)")

        print()
        print("🌐 正在打开HTML报告...")

        # 尝试打开HTML报告
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", "htmlcov/index.html"])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["start", "htmlcov/index.html"])
            else:  # Linux
                subprocess.run(["xdg-open", "htmlcov/index.html"])
            print("✅ HTML报告已打开")
        except Exception as e:
            print(f"❌ 无法打开HTML报告: {e}")
            print(f"请手动打开: {os.path.abspath('htmlcov/index.html')}")

        return True

    except FileNotFoundError:
        print("❌ 无法读取覆盖率数据")
        return False


def generate_coverage():
    """生成覆盖率报告"""
    print("🔄 正在生成覆盖率报告...")
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "--cov=src/app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=json",
        ],
        capture_output=False,
        text=True,
    )

    if result.returncode == 0:
        print("✅ 覆盖率报告生成完成")
        return True
    else:
        print("❌ 覆盖率报告生成失败")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        generate_coverage()
    else:
        view_coverage()
