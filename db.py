import sqlite3
from datetime import date
from pathlib import Path

from config import DATABASE_PATH


class Database:
    """负责 SQLite 数据库操作。"""

    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

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
            conn.execute(
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

            cursor = conn.execute(
                """
                SELECT id
                FROM repositories
                WHERE full_name = ?
                """,
                (repo["full_name"],),
            )

            row = cursor.fetchone()

            if row is None:
                raise RuntimeError(
                    "保存仓库后无法获取数据库 ID。"
                )

            return row[0]

    def save_daily_stats(
        self,
        repository_id: int,
        stars: int,
        forks: int,
        open_issues: int,
        commit_count: int,
        contributor_count: int,
        stat_date: str | None = None,
    ) -> None:
        """保存指定日期的统计数据。"""

        if stat_date is None:
            stat_date = date.today().isoformat()

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

                ON CONFLICT(repository_id, stat_date)
                DO UPDATE SET
                    stars = excluded.stars,
                    forks = excluded.forks,
                    open_issues = excluded.open_issues,
                    commit_count = excluded.commit_count,
                    contributor_count = excluded.contributor_count
                """,
                (
                    repository_id,
                    stat_date,
                    stars,
                    forks,
                    open_issues,
                    commit_count,
                    contributor_count,
                ),
            )

    def get_daily_stats(
        self,
        repository_id: int,
    ) -> list[tuple]:
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

    def get_repositories(self) -> list[tuple]:
        """获取所有已经追踪的仓库。"""

        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT
                    id,
                    full_name
                FROM repositories
                ORDER BY id
                """
            )

            return cursor.fetchall()

    def get_repository_id(
        self,
        repo_name: str,
    ) -> int | None:
        """根据仓库名称获取数据库 ID。"""

        with self._connect() as conn:
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
                return None

            return row[0]


if __name__ == "__main__":
    database = Database()

    print("数据库初始化成功！")
    print(f"数据库位置：{database.db_path}")