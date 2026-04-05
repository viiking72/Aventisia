"""HTTP client for GitHub REST API (resources used by this connector)."""
from typing import Any

import httpx

GITHUB_API_BASE = "https://api.github.com"
GITHUB_JSON = "application/vnd.github+json"
API_VERSION = "2022-11-28"


class GitHubApiError(Exception):
    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"GitHub API {status_code}: {body}")


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": GITHUB_JSON,
        "X-GitHub-Api-Version": API_VERSION,
    }


class GitHubClient:
    def __init__(self, base_url: str = GITHUB_API_BASE, *, timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    async def list_user_repos(self, token: str) -> list[str]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self._base}/user/repos",
                headers=_headers(token),
                params={"per_page": 100, "sort": "updated"},
                timeout=self._timeout,
            )
        raw = self._json_list(r)
        return [
            str(item["full_name"])
            for item in raw
            if isinstance(item, dict) and item.get("full_name") is not None
        ]

    async def list_repo_issues(self, token: str, owner: str, repo: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self._base}/repos/{owner}/{repo}/issues",
                headers=_headers(token),
                params={"per_page": 50, "state": "all"},
                timeout=self._timeout,
            )
        raw = self._json_list(r)
        slim: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            if "number" not in item or "title" not in item:
                continue
            slim.append(
                {
                    "number": item["number"],
                    "title": item["title"],
                    "body": item.get("body"),
                }
            )
        return slim

    async def create_issue(
        self,
        token: str,
        owner: str,
        repo: str,
        *,
        title: str,
        body: str | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"title": title}
        if body is not None:
            payload["body"] = body
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self._base}/repos/{owner}/{repo}/issues",
                headers=_headers(token),
                json=payload,
                timeout=self._timeout,
            )
        return self._json_object(r, ok=(200, 201))

    def _json_list(self, r: httpx.Response) -> list[dict[str, Any]]:
        if r.status_code != 200:
            raise GitHubApiError(r.status_code, r.text)
        return r.json()

    def _json_object(self, r: httpx.Response, *, ok: tuple[int, ...]) -> dict[str, Any]:
        if r.status_code not in ok:
            raise GitHubApiError(r.status_code, r.text)
        return r.json()
