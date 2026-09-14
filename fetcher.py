from datetime import datetime, timedelta, timezone

import requests

from config import GITHUB_API_URL, GITHUB_TOKEN


class GitHubFetcher:
    """负责从 GitHub API 获取数据。"""

    def __init__(self) -> None:
        self.base_url = GITHUB_API_URL
        self.token = GITHUB_TOKEN

    def _get_headers(self) -> dict:
        """生成 GitHub API 请求头。"""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    def get_repository(self, repo_name: str) -> dict:
        """获取 GitHub 仓库基本信息。"""
        url = f"{self.base_url}/repos/{repo_name}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 404:
                raise ValueError(
                    f"仓库不存在：{repo_name}"
                )

            if response.status_code == 403:
                raise RuntimeError(
                    "GitHub API 请求受限，可能触发了速率限制。"
                )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            raise RuntimeError(
                "请求 GitHub 超时，请检查网络。"
            )

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "无法连接 GitHub，请检查网络连接。"
            )

    def get_repository_data(
        self,
        repo_name: str,
    ) -> dict:
        """获取仓库需要保存的数据。"""
        repo = self.get_repository(repo_name)

        return {
            "full_name": repo["full_name"],
            "name": repo["name"],
            "description": repo["description"],
            "stargazers_count": repo["stargazers_count"],
            "forks_count": repo["forks_count"],
            "open_issues_count": repo["open_issues_count"],
            "created_at": repo["created_at"],
            "updated_at": repo["updated_at"],
        }

    def get_recent_commits(
        self,
        repo_name: str,
        days: int = 30,
    ) -> list[dict]:
        """获取指定仓库最近几天的 Commit。"""
        url = f"{self.base_url}/repos/{repo_name}/commits"

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        params = {
            "since": start_time.isoformat(),
            "until": end_time.isoformat(),
            "per_page": 100,
        }

        commits: list[dict] = []
        page = 1

        while True:
            params["page"] = page

            try:
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10,
                )

                if response.status_code == 404:
                    raise ValueError(
                        f"仓库不存在：{repo_name}"
                    )

                if response.status_code == 403:
                    raise RuntimeError(
                        "GitHub API 请求受限，可能触发了速率限制。"
                    )

                response.raise_for_status()

                page_commits = response.json()

                if not page_commits:
                    break

                commits.extend(page_commits)

                if len(page_commits) < 100:
                    break

                page += 1

            except requests.exceptions.Timeout:
                raise RuntimeError(
                    "请求 GitHub 超时，请检查网络。"
                )

            except requests.exceptions.ConnectionError:
                raise RuntimeError(
                    "无法连接 GitHub，请检查网络连接。"
                )

        return commits

    def get_contributors(
        self,
        repo_name: str,
    ) -> list[dict]:
        """获取仓库贡献者。"""
        url = (
            f"{self.base_url}/repos/"
            f"{repo_name}/contributors"
        )

        contributors: list[dict] = []
        page = 1

        while True:
            params = {
                "per_page": 100,
                "page": page,
            }

            try:
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10,
                )

                if response.status_code == 404:
                    raise ValueError(
                        f"仓库不存在：{repo_name}"
                    )

                if response.status_code == 403:
                    raise RuntimeError(
                        "GitHub API 请求受限，可能触发了速率限制。"
                    )

                response.raise_for_status()

                page_contributors = response.json()

                if not page_contributors:
                    break

                contributors.extend(
                    page_contributors
                )

                if len(page_contributors) < 100:
                    break

                page += 1

            except requests.exceptions.Timeout:
                raise RuntimeError(
                    "请求 GitHub 超时，请检查网络。"
                )

            except requests.exceptions.ConnectionError:
                raise RuntimeError(
                    "无法连接 GitHub，请检查网络连接。"
                )

        return contributors


if __name__ == "__main__":
    fetcher = GitHubFetcher()

    repo_name = "psf/requests"

    print("正在测试 GitHub API...")

    repo = fetcher.get_repository(
        repo_name
    )

    print(
        "项目名称:",
        repo["name"],
    )

    print(
        "Stars:",
        repo["stargazers_count"],
    )

    print(
        "Forks:",
        repo["forks_count"],
    )

    print(
        "Open Issues:",
        repo["open_issues_count"],
    )

    print(
        "Description:",
        repo["description"],
    )

    commits = fetcher.get_recent_commits(
        repo_name
    )

    print(
        "最近30天 Commit 数量:",
        len(commits),
    )

    contributors = fetcher.get_contributors(
        repo_name
    )

    print(
        "贡献者数量:",
        len(contributors),
    )