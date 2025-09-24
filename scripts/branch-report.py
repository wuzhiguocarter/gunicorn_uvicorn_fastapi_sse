#!/usr/bin/env python3
"""
分支报告脚本
生成分支状态和管理报告
"""

import subprocess
from datetime import datetime
from typing import Any


class BranchReporter:
    """分支报告生成器"""

    def __init__(self):
        self.report_file = "branch-report.md"
        self.branches = []

    def get_branches(self) -> list[dict[str, Any]]:
        """获取所有分支信息"""
        try:
            # 获取所有分支
            result = subprocess.run(
                [
                    "git",
                    "branch",
                    "-a",
                    "--format=%(refname:short)|%(objectname)|%(committerdate)",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            branches = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) != 3:
                    continue

                name, sha, date_str = parts

                # 清理分支名称
                name = name.strip()
                if name.startswith("* "):
                    name = name[2:]

                # 解析日期
                try:
                    commit_date = datetime.fromisoformat(date_str.replace(" ", "T"))
                except ValueError:
                    commit_date = datetime.now()

                # 计算年龄
                age_days = (datetime.now() - commit_date).days

                # 确定分支类型
                branch_type = self.get_branch_type(name)

                branches.append(
                    {
                        "name": name,
                        "sha": sha,
                        "commit_date": commit_date,
                        "age_days": age_days,
                        "type": branch_type,
                        "is_remote": name.startswith("origin/"),
                        "is_current": name.startswith("* "),
                    }
                )

            return sorted(branches, key=lambda x: x["age_days"], reverse=True)

        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting branches: {e}")
            return []

    def get_branch_type(self, branch_name: str) -> str:
        """确定分支类型"""
        # 移除远程前缀
        if branch_name.startswith("origin/"):
            branch_name = branch_name[7:]

        if branch_name in ["main", "master"]:
            return "main"
        elif branch_name == "develop":
            return "develop"
        elif branch_name.startswith("feature/"):
            return "feature"
        elif branch_name.startswith("hotfix/"):
            return "hotfix"
        elif branch_name.startswith("release/"):
            return "release"
        elif branch_name.startswith("experiment/"):
            return "experiment"
        else:
            return "other"

    def get_branch_statistics(self) -> dict[str, Any]:
        """获取分支统计信息"""
        stats = {
            "total": len(self.branches),
            "by_type": {},
            "by_age": {
                "recent": 0,  # < 7 days
                "moderate": 0,  # 7-30 days
                "old": 0,  # > 30 days
            },
            "remote_vs_local": {
                "remote": 0,
                "local": 0,
            },
        }

        for branch in self.branches:
            # 按类型统计
            branch_type = branch["type"]
            stats["by_type"][branch_type] = stats["by_type"].get(branch_type, 0) + 1

            # 按年龄统计
            age = branch["age_days"]
            if age < 7:
                stats["by_age"]["recent"] += 1
            elif age < 30:
                stats["by_age"]["moderate"] += 1
            else:
                stats["by_age"]["old"] += 1

            # 远程vs本地统计
            if branch["is_remote"]:
                stats["remote_vs_local"]["remote"] += 1
            else:
                stats["remote_vs_local"]["local"] += 1

        return stats

    def generate_branch_table(self, branches: list[dict[str, Any]]) -> str:
        """生成分支表格"""
        if not branches:
            return "No branches found."

        table_lines = [
            "| 分支名称 | 类型 | 年龄(天) | 最后提交 | 状态 |",
            "|----------|------|----------|----------|------|",
        ]

        for branch in branches[:20]:  # 只显示前20个分支
            name = branch["name"]
            if len(name) > 30:
                name = name[:27] + "..."

            status = (
                "🟢"
                if branch["age_days"] < 7
                else "🟡"
                if branch["age_days"] < 30
                else "🔴"
            )

            table_lines.append(
                f"| {name} | {branch['type']} | {branch['age_days']} | "
                f"{branch['commit_date'].strftime('%Y-%m-%d')} | {status} |"
            )

        if len(branches) > 20:
            table_lines.append(f"\n... and {len(branches) - 20} more branches")

        return "\n".join(table_lines)

    def generate_recommendations(self, stats: dict[str, Any]) -> str:
        """生成建议"""
        recommendations = []

        # 检查过期分支
        if stats["by_age"]["old"] > 5:
            recommendations.append(
                f"🧹 有 {stats['by_age']['old']} 个分支超过30天未更新，建议清理"
            )

        # 检查实验分支
        experiment_count = stats["by_type"].get("experiment", 0)
        if experiment_count > 3:
            recommendations.append(
                f"🧪 有 {experiment_count} 个实验分支，建议 review 并清理"
            )

        # 检查功能分支
        feature_count = stats["by_type"].get("feature", 0)
        if feature_count > 10:
            recommendations.append(f"🚀 有 {feature_count} 个功能分支，建议及时合并")

        # 检查远程分支
        remote_ratio = (
            stats["remote_vs_local"]["remote"] / stats["total"] * 100
            if stats["total"] > 0
            else 0
        )
        if remote_ratio > 60:
            recommendations.append(
                f"🌐 {remote_ratio:.1f}% 的分支是远程分支，建议清理已合并的远程分支"
            )

        if not recommendations:
            recommendations.append("✅ 分支状态良好，无需特别处理")

        return "\n".join(f"- {rec}" for rec in recommendations)

    def generate_report(self) -> str:
        """生成完整报告"""
        self.branches = self.get_branches()
        stats = self.get_branch_statistics()

        report = f"""# 📊 分支管理报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**仓库**: {subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()}

## 📈 总体统计

- **总分支数**: {stats["total"]}
- **本地分支**: {stats["remote_vs_local"]["local"]}
- **远程分支**: {stats["remote_vs_local"]["remote"]}

### 📊 按类型分布
"""

        for branch_type, count in stats["by_type"].items():
            report += f"\n- **{branch_type}**: {count}"

        report += f"""

### 📅 按年龄分布
- **最近更新** (< 7天): {stats["by_age"]["recent"]} 🟢
- **中等更新** (7-30天): {stats["by_age"]["moderate"]} 🟡
- **长期未更新** (> 30天): {stats["by_age"]["old"]} 🔴

## 📋 分支详情

### 主要分支
"""

        # 主要分支
        main_branches = [b for b in self.branches if b["type"] in ["main", "develop"]]
        if main_branches:
            report += "\n" + self.generate_branch_table(main_branches)
        else:
            report += "\n未找到主要分支"

        # 功能分支
        feature_branches = [b for b in self.branches if b["type"] == "feature"]
        report += f"\n### 功能分支 ({len(feature_branches)})"
        if feature_branches:
            report += "\n" + self.generate_branch_table(feature_branches)
        else:
            report += "\n未找到功能分支"

        # 修复分支
        hotfix_branches = [b for b in self.branches if b["type"] == "hotfix"]
        report += f"\n### 修复分支 ({len(hotfix_branches)})"
        if hotfix_branches:
            report += "\n" + self.generate_branch_table(hotfix_branches)
        else:
            report += "\n未找到修复分支"

        # 实验分支
        experiment_branches = [b for b in self.branches if b["type"] == "experiment"]
        report += f"\n### 实验分支 ({len(experiment_branches)})"
        if experiment_branches:
            report += "\n" + self.generate_branch_table(experiment_branches)
        else:
            report += "\n未找到实验分支"

        # 建议
        report += "\n## 💡 改进建议\n\n"
        report += self.generate_recommendations(stats)

        report += """

## 📝 备注

- 🟢 分支最近7天内有更新
- 🟡 分支7-30天内有更新
- 🔴 分支超过30天未更新
- 建议定期清理已合并和过期的分支
- 遵循分支命名规范以提高管理效率

---
*此报告由自动化工具体生成*
"""

        return report

    def save_report(self, report: str) -> None:
        """保存报告到文件"""
        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📄 报告已保存到: {self.report_file}")

    def display_report(self, report: str) -> None:
        """显示报告"""
        print("\n" + "=" * 60)
        print("📊 BRANCH MANAGEMENT REPORT")
        print("=" * 60)
        print(report)

    def run(self) -> None:
        """运行报告生成"""
        print("🔍 Generating branch report...")
        report = self.generate_report()
        self.save_report(report)
        self.display_report(report)


def main():
    """主函数"""
    reporter = BranchReporter()
    reporter.run()


if __name__ == "__main__":
    main()
