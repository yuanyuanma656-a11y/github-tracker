from collections import Counter

from analytics import Analytics
from cli import parse_args
from db import Database
from fetcher import GitHubFetcher
from logger import logger


def add_repository(
    repo_name: str,
    fetcher: GitHubFetcher,
    database: Database,
) -> None:
    """添加并保存一个 GitHub 仓库。"""

    logger.info("开始添加仓库：%s", repo_name)

    print(f"正在获取仓库：{repo_name}")

    # 获取仓库信息
    repo = fetcher.get_repository_data(repo_name)

    logger.info(
        "成功获取仓库信息：%s",
        repo["full_name"],
    )

    print("仓库信息获取成功")
    print(f"名称：{repo['full_name']}")
    print(f"Stars：{repo['stargazers_count']}")
    print(f"Forks：{repo['forks_count']}")
    print(f"Open Issues：{repo['open_issues_count']}")

    # 保存仓库
    repository_id = database.save_repository(repo)

    logger.info(
        "仓库保存成功：%s，ID=%s",
        repo_name,
        repository_id,
    )

    print(f"仓库已保存，数据库 ID：{repository_id}")

    # 获取最近 30 天 Commit
    print("正在获取最近 30 天 Commit...")

    commits = fetcher.get_recent_commits(
        repo_name,
        days=30,
    )

    logger.info(
        "获取 Commit 成功：%s，数量=%s",
        repo_name,
        len(commits),
    )

    print(
        f"最近 30 天 Commit：{len(commits)}"
    )

    # 按日期统计 Commit
    daily_commit_counts = Counter()

    for commit in commits:
        commit_date = get_commit_date(commit)

        if commit_date:
            daily_commit_counts[commit_date] += 1

    print("\n最近 30 天每日 Commit：")

    for stat_date in sorted(daily_commit_counts):
        print(
            f"  {stat_date}: "
            f"{daily_commit_counts[stat_date]}"
        )

    # 获取贡献者
    print("\n正在获取贡献者...")

    contributors = fetcher.get_contributors(repo_name)

    contributor_count = len(contributors)

    logger.info(
        "获取贡献者成功：%s，数量=%s",
        repo_name,
        contributor_count,
    )

    print(
        f"贡献者数量：{contributor_count}"
    )

    # 保存每天的统计数据
    save_daily_commit_stats(
        database=database,
        repository_id=repository_id,
        repo=repo,
        daily_commit_counts=daily_commit_counts,
        contributor_count=contributor_count,
    )

    print("\n每日统计数据保存成功！")
    print("添加仓库完成！")

    logger.info(
        "仓库添加完成：%s",
        repo_name,
    )


def get_commit_date(
    commit: dict,
) -> str | None:
    """从 Commit 数据中获取日期。"""

    commit_data = commit.get("commit", {})

    author_data = commit_data.get("author")

    if not author_data:
        return None

    commit_datetime = author_data.get("date")

    if not commit_datetime:
        return None

    return commit_datetime[:10]


def save_daily_commit_stats(
    database: Database,
    repository_id: int,
    repo: dict,
    daily_commit_counts: Counter,
    contributor_count: int,
) -> None:
    """保存最近 30 天每天的统计数据。"""

    # 没有 Commit 的日期也要保存为 0
    commits = daily_commit_counts

    if commits:
        first_date = min(commits)
        last_date = max(commits)
    else:
        from datetime import date, timedelta

        last_date = date.today().isoformat()

        first_date = (
            date.today() - timedelta(days=29)
        ).isoformat()

    from datetime import date, timedelta

    start_date = date.fromisoformat(first_date)
    end_date = date.fromisoformat(last_date)

    current_date = start_date

    while current_date <= end_date:
        stat_date = current_date.isoformat()

        commit_count = commits.get(
            stat_date,
            0,
        )

        database.save_daily_stats(
            repository_id=repository_id,
            stars=repo["stargazers_count"],
            forks=repo["forks_count"],
            open_issues=repo["open_issues_count"],
            commit_count=commit_count,
            contributor_count=contributor_count,
            stat_date=stat_date,
        )

        current_date += timedelta(days=1)


def update_repositories(
    fetcher: GitHubFetcher,
    database: Database,
) -> None:
    """更新所有已经追踪的仓库。"""

    logger.info("开始更新所有仓库")

    repositories = database.get_repositories()

    if not repositories:
        print("目前没有正在追踪的仓库。")
        return

    print(
        f"发现 {len(repositories)} 个仓库，"
        "开始更新...\n"
    )

    success_count = 0
    failed_count = 0

    for repository_id, repo_name in repositories:
        print("=" * 50)

        try:
            add_repository(
                repo_name,
                fetcher,
                database,
            )

            success_count += 1

            print(
                f"✓ {repo_name} 更新成功"
            )

        except Exception as error:
            failed_count += 1

            logger.exception(
                "仓库更新失败：%s",
                repo_name,
            )

            print(
                f"✗ {repo_name} "
                f"更新失败：{error}"
            )

        print()

    print("=" * 50)
    print("更新完成")
    print(f"成功：{success_count}")
    print(f"失败：{failed_count}")


def generate_report(
    repo_name: str,
    database: Database,
) -> None:
    """生成仓库分析报告。"""

    logger.info(
        "开始生成报告：%s",
        repo_name,
    )

    repository_id = database.get_repository_id(
        repo_name
    )

    if repository_id is None:
        print(
            f"数据库中没有找到仓库：{repo_name}"
        )
        print(
            "请先使用 add 命令添加仓库。"
        )
        return

    analytics = Analytics(database)

    print("正在生成 Commit 图表...")

    chart_path = analytics.generate_commit_chart(
        repository_id,
        repo_name,
    )

    print(
        f"图表生成成功：{chart_path}"
    )

    print("正在生成 Markdown 报告...")

    report_path = (
        analytics.generate_markdown_report(
            repository_id,
            repo_name,
        )
    )

    print(
        f"报告生成成功：{report_path}"
    )

    print("\n报告生成完成！")

    logger.info(
        "报告生成完成：%s",
        repo_name,
    )


def main() -> None:
    """程序入口。"""

    args = parse_args()

    fetcher = GitHubFetcher()
    database = Database()

    logger.info(
        "程序启动，命令=%s",
        args.command,
    )

    try:
        if args.command == "add":
            add_repository(
                args.repo,
                fetcher,
                database,
            )

        elif args.command == "update":
            update_repositories(
                fetcher,
                database,
            )

        elif args.command == "report":
            generate_report(
                args.repo,
                database,
            )

    except KeyboardInterrupt:
        logger.warning(
            "用户取消程序"
        )

        print("\n程序已取消。")

    except Exception as error:
        logger.exception(
            "程序运行出现异常：%s",
            error,
        )

        print(
            f"\n程序运行失败：{error}"
        )

    finally:
        logger.info("程序结束")


if __name__ == "__main__":
    main()