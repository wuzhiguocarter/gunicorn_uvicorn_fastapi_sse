#!/usr/bin/env python3
"""
Git Hooks安装脚本
自动安装和配置Git Hooks
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


class GitHookInstaller:
    """Git Hook安装器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.hooks_dir = self.project_root / ".git" / "hooks"
        self.scripts_dir = self.project_root / "scripts"

    def check_git_repo(self) -> bool:
        """检查是否为Git仓库"""
        git_dir = self.project_root / ".git"
        return git_dir.exists()

    def backup_existing_hooks(self) -> None:
        """备份现有的hooks"""
        backup_dir = self.hooks_dir / "backup"
        backup_dir.mkdir(exist_ok=True)

        for hook_file in self.hooks_dir.glob("*.sample"):
            if hook_file.stem not in ["pre-commit", "commit-msg", "pre-push"]:
                continue

            backup_file = backup_dir / hook_file.name
            if not backup_file.exists():
                shutil.copy2(hook_file, backup_file)
                print(f"📦 备份现有hook: {hook_file.name}")

    def install_pre_commit_hook(self) -> None:
        """安装pre-commit hook"""
        hook_path = self.hooks_dir / "pre-commit"
        hook_content = """#!/bin/bash
# Pre-commit hook
echo "🔍 Running pre-commit checks..."

# 优先使用pre-commit工具（如果安装了）
if command -v pre-commit &> /dev/null; then
    echo "🔧 Using pre-commit tool..."
    pre-commit run --all-files
    if [ $? -ne 0 ]; then
        echo "❌ Pre-commit checks failed"
        exit 1
    fi
else
    echo "📝 Running manual code quality checks..."

    # 运行ruff格式化检查
    if command -v ruff &> /dev/null; then
        ruff check --diff .
        if [ $? -ne 0 ]; then
            echo "❌ Ruff formatting issues found"
            echo "   Run 'ruff check --fix .' to fix formatting issues"
            exit 1
        fi
    else
        echo "⚠️  ruff not found, skipping..."
    fi

    # 运行ruff linting
    if command -v ruff &> /dev/null; then
        ruff check .
        if [ $? -ne 0 ]; then
            echo "❌ Ruff linting failed"
            exit 1
        fi
    else
        echo "⚠️  ruff not found, skipping..."
    fi

    # 运行mypy类型检查
    if command -v mypy &> /dev/null; then
        mypy src/app/
        if [ $? -ne 0 ]; then
            echo "❌ MyPy type checking failed"
            exit 1
        fi
    else
        echo "⚠️  mypy not found, skipping..."
    fi
fi

# 运行测试
echo "🧪 Running tests..."
if command -v uv &> /dev/null; then
    uv run pytest src/tests/ -v
else
    python -m pytest src/tests/ -v
fi

if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi

echo "✅ Pre-commit checks passed"
"""

        with open(hook_path, "w") as f:
            f.write(hook_content)

        os.chmod(hook_path, 0o755)
        print("✅ 安装 pre-commit hook")

    def install_commit_msg_hook(self) -> None:
        """安装commit-msg hook"""
        hook_path = self.hooks_dir / "commit-msg"
        hook_content = """#!/bin/bash
# Commit message hook
echo "📝 Validating commit message..."

# 运行commitlint
if [ -f "node_modules/.bin/commitlint" ]; then
    ./node_modules/.bin/commitlint --edit $1
    if [ $? -ne 0 ]; then
        echo "❌ Commit message validation failed"
        echo "   请遵循以下格式: <type>(<scope>): <subject>"
        echo "   例如: feat(auth): add user login functionality"
        echo "   支持的类型: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert"
        exit 1
    fi
elif command -v commitlint &> /dev/null; then
    commitlint --edit $1
    if [ $? -ne 0 ]; then
        echo "❌ Commit message validation failed"
        echo "   请遵循以下格式: <type>(<scope>): <subject>"
        echo "   例如: feat(auth): add user login functionality"
        exit 1
    fi
else
    echo "⚠️  commitlint not found. 请运行: npm install"
fi

echo "✅ Commit message validation passed"
"""

        with open(hook_path, "w") as f:
            f.write(hook_content)

        os.chmod(hook_path, 0o755)
        print("✅ 安装 commit-msg hook")

    def install_pre_push_hook(self) -> None:
        """安装pre-push hook"""
        hook_path = self.hooks_dir / "pre-push"
        hook_content = """#!/bin/bash
# Pre-push hook
echo "🚀 Running pre-push checks..."

# 验证分支名称
python scripts/validate-branch-name.py
if [ $? -ne 0 ]; then
    echo "❌ Branch name validation failed"
    exit 1
fi

# 运行快速检查
echo "⚡ Running fast checks..."

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes"
    echo "   Consider committing them before pushing"
fi

# 检查是否在正确的分支上
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo "🔒 Pushing to main branch - ensure this is intentional"
fi

echo "✅ Pre-push checks passed"
"""

        with open(hook_path, "w") as f:
            f.write(hook_content)

        os.chmod(hook_path, 0o755)
        print("✅ 安装 pre-push hook")

    def install_prepare_commit_msg_hook(self) -> None:
        """安装prepare-commit-msg hook"""
        hook_path = self.hooks_dir / "prepare-commit-msg"
        hook_content = """#!/bin/bash
# Prepare commit message hook
echo "📝 Preparing commit message template..."

# 如果是合并提交，不处理
if [ "$2" = "merge" ]; then
    exit 0
fi

# 如果是squash提交，不处理
if [ "$2" = "squash" ]; then
    exit 0
fi

# 如果提交消息已经存在，不处理
if [ -s "$1" ]; then
    exit 0
fi

# 获取当前分支名称
BRANCH_NAME=$(git branch --show-current)
TICKET_NUMBER=$(echo $BRANCH_NAME | grep -oE '[0-9]+$' | tail -1)

# 如果找到任务号，添加到提交消息
if [ -n "$TICKET_NUMBER" ]; then
    echo "# #$TICKET_NUMBER" >> "$1"
    echo "" >> "$1"
    echo "# 请选择提交类型:" >> "$1"
    echo "# feat: 新功能" >> "$1"
    echo "# fix: 修复bug" >> "$1"
    echo "# docs: 文档更新" >> "$1"
    echo "# style: 代码格式调整" >> "$1"
    echo "# refactor: 重构代码" >> "$1"
    echo "# test: 测试相关" >> "$1"
    echo "# chore: 构建或工具变动" >> "$1"
fi
"""

        with open(hook_path, "w") as f:
            f.write(hook_content)

        os.chmod(hook_path, 0o755)
        print("✅ 安装 prepare-commit-msg hook")

    def setup_pre_commit(self) -> None:
        """设置pre-commit配置"""
        try:
            subprocess.run(["pre-commit", "install"], check=True)
            print("✅ 安装 pre-commit")
        except subprocess.CalledProcessError:
            print("⚠️  pre-commit安装失败，请手动安装: pip install pre-commit")

    def create_git_config(self) -> None:
        """创建Git配置"""
        git_config = {
            "commit.template": ".gitmessage",
            "core.hooksPath": ".git/hooks",
            "branch.autosetuprebase": "always",
            "pull.rebase": "true",
        }

        for key, value in git_config.items():
            try:
                subprocess.run(
                    ["git", "config", "--local", key, value],
                    check=True,
                    capture_output=True,
                )
                print(f"✅ 设置 git config {key} = {value}")
            except subprocess.CalledProcessError:
                print(f"⚠️  设置 git config {key} 失败")

    def create_commit_template(self) -> None:
        """创建提交模板"""
        template_path = self.project_root / ".gitmessage"
        template_content = """# <type>(<scope>): <subject>
#
# # 空行
# # body (可选)
#
# # 空行
# # footer (可选)
#
# # 类型说明:
# # feat: 新功能
# # fix: 修复bug
# # docs: 文档更新
# # style: 代码格式调整
# # refactor: 重构代码
# # test: 测试相关
# # chore: 构建或工具变动
# # perf: 性能优化
# # ci: CI配置修改
# # build: 构建系统修改
# # revert: 代码回滚
#
# # 示例:
# # feat(auth): add user login functionality
# # fix(api): resolve memory leak in request handler
# # docs(readme): update installation instructions
"""

        with open(template_path, "w") as f:
            f.write(template_content)
        print("✅ 创建提交模板")

    def check_dependencies(self) -> dict:
        """检查依赖状态"""
        dependencies = {
            "npm": False,
            "commitlint_local": False,
            "commitlint_global": False,
            "uv": False,
            "python": False,
            "pre_commit": False,
        }

        # 检查 Node.js/npm
        try:
            subprocess.run(["npm", "--version"], check=True, capture_output=True)
            dependencies["npm"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 检查本地 commitlint
        if Path("node_modules/.bin/commitlint").exists():
            dependencies["commitlint_local"] = True

        # 检查全局 commitlint
        try:
            subprocess.run(["commitlint", "--version"], check=True, capture_output=True)
            dependencies["commitlint_global"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 检查 uv
        try:
            subprocess.run(["uv", "--version"], check=True, capture_output=True)
            dependencies["uv"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 检查 Python
        try:
            subprocess.run(["python", "--version"], check=True, capture_output=True)
            dependencies["python"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 检查 pre-commit
        try:
            subprocess.run(["pre-commit", "--version"], check=True, capture_output=True)
            dependencies["pre_commit"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return dependencies

    def install_hooks(self) -> None:
        """安装所有hooks"""
        print("🔧 开始安装 Git Hooks...")

        if not self.check_git_repo():
            print("❌ 当前目录不是Git仓库")
            sys.exit(1)

        # 检查依赖
        deps = self.check_dependencies()
        print("\n📦 依赖检查:")
        print(f"   • npm: {'✅' if deps['npm'] else '❌'}")
        print(f"   • commitlint (本地): {'✅' if deps['commitlint_local'] else '❌'}")
        print(f"   • commitlint (全局): {'✅' if deps['commitlint_global'] else '❌'}")
        print(f"   • uv: {'✅' if deps['uv'] else '❌'}")
        print(f"   • pre-commit: {'✅' if deps['pre_commit'] else '❌'}")

        # 创建hooks目录
        self.hooks_dir.mkdir(exist_ok=True)

        # 备份现有hooks
        self.backup_existing_hooks()

        # 安装hooks
        self.install_pre_commit_hook()
        self.install_commit_msg_hook()
        self.install_pre_push_hook()
        self.install_prepare_commit_msg_hook()

        # 设置pre-commit
        if deps["pre_commit"]:
            self.setup_pre_commit()

        # 创建Git配置
        self.create_git_config()

        # 创建提交模板
        self.create_commit_template()

        # 给出建议
        print("\n💡 建议:")
        if not deps["commitlint_local"] and deps["npm"]:
            print("   • 建议运行: npm install (安装 commitlint)")
        if not deps["pre_commit"]:
            print("   • 建议运行: pip install pre-commit")
        if not deps["uv"]:
            print("   • 建议安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh")

        print("\n🎉 Git Hooks 安装完成!")
        print("\n📋 已安装的hooks:")
        print("   • pre-commit: 提交前检查代码质量 (pre-commit工具 或 ruff + mypy + pytest)")
        print("   • commit-msg: 验证提交消息格式 (commitlint)")
        print("   • pre-push: 推送前验证分支名称和快速检查")
        print("   • prepare-commit-msg: 准备提交消息模板")
        print("\n🔧 相关配置:")
        print("   • 创建了提交模板 (.gitmessage)")
        print("   • 设置了Git配置选项")
        print("   • 配置了pre-commit工具")
        print("\n📦 依赖要求:")
        print("   • Node.js依赖: npm install (commitlint)")
        print("   • Python依赖: uv pip install -e '.[dev]'")
        print("   • Git hooks: 已安装到 .git/hooks/")

    def uninstall_hooks(self) -> None:
        """卸载hooks"""
        print("🧹 卸载 Git Hooks...")

        hooks_to_remove = ["pre-commit", "commit-msg", "pre-push", "prepare-commit-msg"]

        for hook in hooks_to_remove:
            hook_path = self.hooks_dir / hook
            if hook_path.exists():
                hook_path.unlink()
                print(f"🗑️  删除 {hook}")

        print("✅ Git Hooks 卸载完成")


def main():
    """主函数"""
    installer = GitHookInstaller()

    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        installer.uninstall_hooks()
    else:
        installer.install_hooks()


if __name__ == "__main__":
    main()
