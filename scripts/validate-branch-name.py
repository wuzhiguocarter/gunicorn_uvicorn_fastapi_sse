#!/usr/bin/env python3
"""
Git分支名称验证脚本
验证分支命名是否符合规范
"""

import re
import subprocess
import sys


class BranchValidator:
    """分支名称验证器"""

    def __init__(self):
        # 定义分支命名规范
        self.patterns = {
            "feature": r"^feature/[a-z0-9-]+-\d+$",
            "hotfix": r"^hotfix/[a-z0-9-]+-\d+$",
            "release": r"^release/v\d+\.\d+\.\d+$",
            "experiment": r"^experiment/[a-z0-9-]+-[a-z0-9-]+$",
            "develop": r"^develop$",
            "main": r"^main$",
        }

        # 定义错误消息
        self.error_messages = {
            "feature": "功能分支格式: feature/功能描述-任务号 (如: feature/user-auth-123)",
            "hotfix": "修复分支格式: hotfix/问题描述-任务号 (如: hotfix/memory-leak-456)",
            "release": "发布分支格式: release/v版本号 (如: release/v1.0.0)",
            "experiment": "实验分支格式: experiment/技术方案-开发者 (如: experiment/new-cache-john)",
        }

    def validate_branch_name(self, branch_name: str) -> tuple[bool, str | None]:
        """验证分支名称"""
        # 移除远程分支前缀
        if branch_name.startswith("origin/"):
            branch_name = branch_name[7:]

        # 移除HEAD引用
        if branch_name == "HEAD":
            return True, None

        # 检查每个模式
        for _branch_type, pattern in self.patterns.items():
            if re.match(pattern, branch_name):
                return True, None

        # 检查是否为受保护分支
        if branch_name in ["main", "develop"]:
            return True, None

        return False, self._get_error_message(branch_name)

    def _get_error_message(self, branch_name: str) -> str:
        """获取错误消息"""
        if "/" not in branch_name:
            return "分支名称必须包含类型前缀 (如: feature/, hotfix/, release/)"

        branch_type = branch_name.split("/")[0]
        if branch_type in self.error_messages:
            return f"无效的{branch_type}分支名称: {self.error_messages[branch_type]}"

        return f"未知的分支类型: {branch_type}。支持的类型: feature, hotfix, release, experiment"

    def get_current_branch(self) -> str:
        """获取当前分支名称"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def check_branch_creation(self) -> int:
        """检查分支创建（用于pre-push hook）"""
        current_branch = self.get_current_branch()
        if not current_branch:
            print("❌ 无法获取当前分支名称")
            return 1

        is_valid, error_msg = self.validate_branch_name(current_branch)

        if is_valid:
            print(f"✅ 分支名称有效: {current_branch}")
            return 0
        else:
            print(f"❌ 分支名称无效: {current_branch}")
            print(f"   错误: {error_msg}")
            print("\n正确的分支命名格式:")
            for branch_type, message in self.error_messages.items():
                print(f"   {branch_type}: {message}")
            return 1


def main():
    """主函数"""
    validator = BranchValidator()

    # 如果提供了参数，验证指定分支名称
    if len(sys.argv) > 1:
        branch_name = sys.argv[1]
        is_valid, error_msg = validator.validate_branch_name(branch_name)

        if is_valid:
            print(f"✅ 分支名称有效: {branch_name}")
            sys.exit(0)
        else:
            print(f"❌ 分支名称无效: {branch_name}")
            print(f"   错误: {error_msg}")
            sys.exit(1)

    # 否则检查当前分支
    sys.exit(validator.check_branch_creation())


if __name__ == "__main__":
    main()
