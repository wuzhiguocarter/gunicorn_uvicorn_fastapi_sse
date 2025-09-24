#!/usr/bin/env python3
"""
分支清理脚本
自动清理过期和已合并的分支
"""

import os
import sys
from datetime import datetime
from typing import Any

from github import Github


class BranchCleaner:
    """分支清理器"""

    def __init__(self, token: str = None, repo_name: str = None, dry_run: bool = False):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo_name = repo_name or os.getenv("GITHUB_REPOSITORY")
        self.dry_run = dry_run
        self.github = Github(self.token) if self.token else None

        # 清理规则
        self.rules = {
            "merged_branches": {
                "enabled": True,
                "age_days": 7,
                "exclude_patterns": ["main", "develop", "release/*"],
            },
            "stale_branches": {
                "enabled": True,
                "age_days": 30,
                "exclude_patterns": ["main", "develop", "release/*"],
            },
            "experimental_branches": {
                "enabled": True,
                "age_days": 14,
                "patterns": ["experiment/*"],
            },
        }

    def get_branches(self) -> list[dict[str, Any]]:
        """获取所有分支信息"""
        if not self.github:
            print("❌ GitHub token not provided")
            return []

        try:
            repo = self.github.get_repo(self.repo_name)
            branches = repo.get_branches()

            branch_info = []
            for branch in branches:
                try:
                    commit = branch.commit
                    last_commit_date = commit.commit.author.date
                    age_days = (
                        datetime.now(last_commit_date.tzinfo) - last_commit_date
                    ).days

                    branch_info.append(
                        {
                            "name": branch.name,
                            "sha": commit.sha,
                            "last_commit_date": last_commit_date,
                            "age_days": age_days,
                            "protected": branch.protected,
                        }
                    )
                except Exception as e:
                    print(f"⚠️  Error processing branch {branch.name}: {e}")
                    continue

            return sorted(branch_info, key=lambda x: x["age_days"], reverse=True)

        except Exception as e:
            print(f"❌ Error fetching branches: {e}")
            return []

    def should_exclude_branch(
        self, branch_name: str, exclude_patterns: list[str]
    ) -> bool:
        """检查是否应该排除分支"""
        for pattern in exclude_patterns:
            if pattern.endswith("*"):
                if branch_name.startswith(pattern[:-1]):
                    return True
            else:
                if branch_name == pattern:
                    return True
        return False

    def get_merged_branches(
        self, branches: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """获取已合并的分支"""
        if not self.github:
            return []

        try:
            repo = self.github.get_repo(self.repo_name)
            main_branch = repo.get_branch("main")
            merged_branches = []

            for branch_info in branches:
                branch_name = branch_info["name"]

                # 跳过受保护和排除的分支
                if branch_info["protected"] or self.should_exclude_branch(
                    branch_name, self.rules["merged_branches"]["exclude_patterns"]
                ):
                    continue

                # 检查是否已合并到main
                try:
                    base_commit = main_branch.commit
                    branch_commit = repo.get_commit(branch_info["sha"])

                    # 检查分支是否已合并
                    if repo.merge(base_commit.sha, branch_commit.sha, "squash").merged:
                        if (
                            branch_info["age_days"]
                            >= self.rules["merged_branches"]["age_days"]
                        ):
                            merged_branches.append(branch_info)
                except:
                    # 如果无法检查合并状态，跳过
                    continue

            return merged_branches

        except Exception as e:
            print(f"❌ Error checking merged branches: {e}")
            return []

    def get_stale_branches(
        self, branches: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """获取过期分支"""
        stale_branches = []

        for branch_info in branches:
            branch_name = branch_info["name"]

            # 跳过受保护和排除的分支
            if branch_info["protected"] or self.should_exclude_branch(
                branch_name, self.rules["stale_branches"]["exclude_patterns"]
            ):
                continue

            # 检查是否过期
            if branch_info["age_days"] >= self.rules["stale_branches"]["age_days"]:
                stale_branches.append(branch_info)

        return stale_branches

    def get_experimental_branches(
        self, branches: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """获取实验分支"""
        experimental_branches = []

        for branch_info in branches:
            branch_name = branch_info["name"]

            # 检查是否匹配实验分支模式
            for pattern in self.rules["experimental_branches"]["patterns"]:
                if pattern.endswith("*"):
                    if branch_name.startswith(pattern[:-1]):
                        if (
                            branch_info["age_days"]
                            >= self.rules["experimental_branches"]["age_days"]
                        ):
                            experimental_branches.append(branch_info)
                        break

        return experimental_branches

    def delete_branch(self, branch_name: str) -> bool:
        """删除分支"""
        if not self.github:
            print(f"🔧 Would delete branch: {branch_name}")
            return True

        try:
            repo = self.github.get_repo(self.repo_name)

            if self.dry_run:
                print(f"🔧 [DRY RUN] Would delete branch: {branch_name}")
                return True

            # 获取分支引用
            ref = f"heads/{branch_name}"
            repo.get_git_ref(ref).delete()

            print(f"🗑️  Deleted branch: {branch_name}")
            return True

        except Exception as e:
            print(f"❌ Error deleting branch {branch_name}: {e}")
            return False

    def cleanup_branches(self) -> dict[str, Any]:
        """清理分支"""
        print("🧹 Starting branch cleanup...")

        branches = self.get_branches()
        if not branches:
            return {"success": False, "message": "Failed to fetch branches"}

        results = {
            "total_branches": len(branches),
            "merged": [],
            "stale": [],
            "experimental": [],
            "deleted": [],
            "failed": [],
        }

        # 获取需要清理的分支
        if self.rules["merged_branches"]["enabled"]:
            merged_branches = self.get_merged_branches(branches)
            results["merged"] = merged_branches
            print(f"📋 Found {len(merged_branches)} merged branches to clean")

        if self.rules["stale_branches"]["enabled"]:
            stale_branches = self.get_stale_branches(branches)
            results["stale"] = stale_branches
            print(f"📋 Found {len(stale_branches)} stale branches to clean")

        if self.rules["experimental_branches"]["enabled"]:
            experimental_branches = self.get_experimental_branches(branches)
            results["experimental"] = experimental_branches
            print(
                f"📋 Found {len(experimental_branches)} experimental branches to clean"
            )

        # 执行清理
        all_branches_to_delete = (
            results["merged"] + results["stale"] + results["experimental"]
        )

        for branch_info in all_branches_to_delete:
            branch_name = branch_info["name"]
            age_days = branch_info["age_days"]

            print(f"\n🔄 Processing branch: {branch_name} ({age_days} days old)")

            if self.delete_branch(branch_name):
                results["deleted"].append(branch_name)
            else:
                results["failed"].append(branch_name)

        # 生成摘要
        self.generate_summary(results)

        return results

    def generate_summary(self, results: dict[str, Any]) -> None:
        """生成清理摘要"""
        print("\n" + "=" * 50)
        print("📊 BRANCH CLEANUP SUMMARY")
        print("=" * 50)
        print(f"Total branches analyzed: {results['total_branches']}")
        print(f"Merged branches found: {len(results['merged'])}")
        print(f"Stale branches found: {len(results['stale'])}")
        print(f"Experimental branches found: {len(results['experimental'])}")
        print(f"Branches deleted: {len(results['deleted'])}")
        print(f"Failed deletions: {len(results['failed'])}")

        if results["deleted"]:
            print("\n✅ Deleted branches:")
            for branch_name in results["deleted"]:
                print(f"   - {branch_name}")

        if results["failed"]:
            print("\n❌ Failed to delete:")
            for branch_name in results["failed"]:
                print(f"   - {branch_name}")

        print("\n🔧 Dry run mode:", "ON" if self.dry_run else "OFF")
        print("=" * 50)

    def run(self) -> dict[str, Any]:
        """运行清理"""
        if not self.github and not self.dry_run:
            print("❌ GitHub token is required for actual cleanup")
            print("   Use DRY_RUN=true for testing")
            return {"success": False, "message": "Missing GitHub token"}

        return self.cleanup_branches()


def main():
    """主函数"""
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    cleaner = BranchCleaner(dry_run=dry_run)
    results = cleaner.run()

    if results.get("success", False):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
