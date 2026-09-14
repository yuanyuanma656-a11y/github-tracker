import sqlite3
from datetime import date
from pathlib import Path

from config import DATABASE_PATH
from fetcher import GitHubFetcher


class Database:
    """负责 SQLite 数据库操作。"""

    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path

        # 确保 data 文件夹存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建数据库表
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        """连接数据库。"""
        return sqlite3.connect(self.db_path)

    def _create_tables(self) -> None:
        """创建数据库表。"""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    stars INTEGER DEFAULT 0,
                    forks INTEGER DEFAULT 0,
                    open_issues INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id INTEGER NOT NULL,
                    stat_date TEXT NOT NULL,
                    stars INTEGER DEFAULT 0,
                    forks INTEGER DEFAULT 0,
                    open_issues INTEGER DEFAULT 0,
                    commit_count INTEGER DEFAULT 0,
                    contributor_count INTEGER DEFAULT 0,
                    UNIQUE(repository_id, stat_date),
                    FOREIGN KEY(repository_id)
                        REFERENCES repositories(id)
                )
                """
            )

    def save_repository(self, repo: dict) -> int:
        """保存或更新仓库信息。"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO repositories (
                    full_name,
                    name,
                    description,
                    stars,
                    forks,
                    open_issues,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(full_name) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    stars = excluded.stars,
                    forks = excluded.forks,
                    open_issues = excluded.open_issues,
                    updated_at = excluded.updated_at
                """,
                (
                    repo["full_name"],
                    repo["name"],
                    repo["description"],
                    repo["stargazers_count"],
                    repo["forks_count"],
                    repo["open_issues_count"],
                    repo["created_at"],
                    repo["updated_at"],
                ),
            )

            if cursor.lastrowid:
                return cursor.lastrowid

            cursor = conn.execute(
                "SELECT id FROM repositories WHERE full_name = ?",
                (repo["full_name"],),
            )

            return cursor.fetchone()[0]

    def save_daily_stats(
        self,
        repository_id: int,
        stars: int,
        forks: int,
        open_issues: int,
        commit_count: int,
        contributor_count: int,
    ) -> None:
        """保存当天的仓库统计数据。"""
        today = date.today().isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO daily_stats (
                    repository_id,
                    stat_date,
                    stars,
                    forks,
                    open_issues,
                    commit_count,
                    contributor_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repository_id, stat_date) DO UPDATE SET
                    stars = excluded.stars,
                    forks = excluded.forks,
                    open_issues = excluded.open_issues,
                    commit_count = excluded.commit_count,
                    contributor_count = excluded.contributor_count
                """,
                (
                    repository_id,
                    today,
                    stars,
                    forks,
                    open_issues,
                    commit_count,
                    contributor_count,
                ),
            )

    def get_daily_stats(self, repository_id: int) -> list[tuple]:
        """获取仓库的历史统计数据。"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT
                    stat_date,
                    stars,
                    forks,
                    open_issues,
                    commit_count,
                    contributor_count
                FROM daily_stats
                WHERE repository_id = ?
                ORDER BY stat_date ASC
                """,
                (repository_id,),
            )

            return cursor.fetchall()


if __name__ == "__main__":
    fetcher = GitHubFetcher()
    database = Database()

    # 获取仓库基本信息
    repo = fetcher.get_repository_data("psf/requests")

    # 保存仓库
    repository_id = database.save_repository(repo)

    # 获取最近 30 天 Commit
    commits = fetcher.get_recent_commits("psf/requests")

    # 暂时使用 Commit 数量作为当天统计
    commit_count = len(commits)

    # 暂时使用 0 作为贡献者数量
    contributor_count = 0

    # 保存当天统计
    database.save_daily_stats(
        repository_id=repository_id,
        stars=repo["stargazers_count"],
        forks=repo["forks_count"],
        open_issues=repo["open_issues_count"],
        commit_count=commit_count,
        contributor_count=contributor_count,
    )

    print("仓库保存成功！")
    print("仓库：", repo["full_name"])
    print("Stars：", repo["stargazers_count"])
    print("Forks：", repo["forks_count"])
    print("Open Issues：", repo["open_issues_count"])
    print("最近30天 Commit：", commit_count)
    print("数据库 ID：", repository_id)
    print("今日统计数据保存成功！")