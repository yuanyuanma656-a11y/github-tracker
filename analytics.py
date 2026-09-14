from pathlib import Path

import matplotlib.pyplot as plt

from config import REPORT_DIR
from db import Database


class Analytics:
    """负责数据分析、图表生成和报告生成。"""

    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

        # 确保 reports 文件夹存在
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

    def generate_commit_chart(
        self,
        repository_id: int,
        repo_name: str,
    ) -> Path:
        """生成 Commit 趋势图。"""
        stats = self.database.get_daily_stats(repository_id)

        if not stats:
            raise ValueError("没有找到该仓库的历史统计数据。")

        dates = [row[0] for row in stats]
        commit_counts = [row[4] for row in stats]

        plt.figure(figsize=(10, 5))

        plt.plot(
            dates,
            commit_counts,
            marker="o",
        )

        plt.title(f"{repo_name} - Commit Activity")
        plt.xlabel("Date")
        plt.ylabel("Commit Count")

        plt.xticks(rotation=45)
        plt.tight_layout()

        safe_name = repo_name.replace("/", "_")

        output_path = REPORT_DIR / f"{safe_name}_commit_activity.png"

        plt.savefig(output_path, dpi=150)
        plt.close()

        return output_path

    def generate_markdown_report(
        self,
        repository_id: int,
        repo_name: str,
    ) -> Path:
        """生成 Markdown 报告。"""
        stats = self.database.get_daily_stats(repository_id)

        if not stats:
            raise ValueError("没有找到该仓库的历史统计数据。")

        latest = stats[-1]

        stat_date = latest[0]
        stars = latest[1]
        forks = latest[2]
        open_issues = latest[3]
        commit_count = latest[4]
        contributor_count = latest[5]

        safe_name = repo_name.replace("/", "_")

        report_path = REPORT_DIR / f"{safe_name}_report.md"

        content = f"""# GitHub Repository Report

## Repository

**{repo_name}**

## Latest Statistics

| Metric | Value |
|---|---:|
| Date | {stat_date} |
| Stars | {stars} |
| Forks | {forks} |
| Open Issues | {open_issues} |
| Commits | {commit_count} |
| Contributors | {contributor_count} |

## Commit Activity

![Commit Activity]({safe_name}_commit_activity.png)
"""

        report_path.write_text(
            content,
            encoding="utf-8",
        )

        return report_path


if __name__ == "__main__":
    database = Database()

    # 当前测试仓库
    repo_name = "psf/requests"

    # 获取数据库中的仓库 ID
    with database._connect() as conn:
        cursor = conn.execute(
            """
            SELECT id
            FROM repositories
            WHERE full_name = ?
            """,
            (repo_name,),
        )

        row = cursor.fetchone()

    if row is None:
        raise ValueError(
            "数据库中没有找到 psf/requests，请先运行 db.py。"
        )

    repository_id = row[0]

    analytics = Analytics(database)

    chart_path = analytics.generate_commit_chart(
        repository_id,
        repo_name,
    )

    report_path = analytics.generate_markdown_report(
        repository_id,
        repo_name,
    )

    print("图表生成成功：", chart_path)
    print("报告生成成功：", report_path)