"""
GitHub API client for inspecting repositories, commits, releases, and diffs.
"""

import os
from typing import Any, cast

import httpx


class GitHubAppClient:
    """
    Read-only GitHub client using GitHub App or personal access token.
    """

    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "EDGE-Content-Engine/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def get_repository_details(self, owner: str, repo: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{self.base_url}/repos/{owner}/{repo}", headers=self._headers())
            if res.status_code == 200:
                return cast(dict[str, Any], res.json())
            return {"name": repo, "full_name": f"{owner}/{repo}"}

    async def get_latest_commit(
        self, owner: str, repo: str, branch: str = "main"
    ) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/commits/{branch}",
                headers=self._headers(),
            )
            if res.status_code == 200:
                return cast(dict[str, Any], res.json())
            return {}

    async def get_recent_releases(
        self, owner: str, repo: str, count: int = 5
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/releases?per_page={count}",
                headers=self._headers(),
            )
            if res.status_code == 200:
                return cast(list[dict[str, Any]], res.json())
            return []
