import httpx

from app.core.config import settings

GITHUB_API = "https://api.github.com"


class GitHubClient:
    """Code activity: commits, open/stale PRs, active contributors."""

    def _configured(self) -> bool:
        return bool(settings.github_token and settings.github_repo)

    async def fetch_summary(self, repo: str | None = None) -> dict:
        repo = repo or settings.github_repo
        if not settings.use_mock_data and self._configured():
            return await self._fetch_live(repo)
        return self._mock(repo)

    async def _fetch_live(self, repo: str) -> dict:
        headers = {"Authorization": f"Bearer {settings.github_token}", "Accept": "application/vnd.github+json"}
        async with httpx.AsyncClient(base_url=GITHUB_API, headers=headers, timeout=15) as client:
            commits_resp = await client.get(f"/repos/{repo}/commits", params={"per_page": 20})
            prs_resp = await client.get(f"/repos/{repo}/pulls", params={"state": "open", "per_page": 50})

            commits = commits_resp.json() if commits_resp.status_code == 200 else []
            prs = prs_resp.json() if prs_resp.status_code == 200 else []

            stale_prs = [pr for pr in prs if isinstance(pr, dict) and _is_stale(pr.get("updated_at"))]
            contributors = {c.get("commit", {}).get("author", {}).get("name") for c in commits if isinstance(c, dict)}

            return {
                "source": "github",
                "repo": repo,
                "recent_commit_count": len(commits),
                "active_contributors": len([c for c in contributors if c]),
                "open_pull_requests": len(prs),
                "stale_pull_requests": len(stale_prs),
            }

    def _mock(self, repo: str | None) -> dict:
        return {
            "source": "github",
            "repo": repo or "acme/delivery-app",
            "recent_commit_count": 47,
            "active_contributors": 6,
            "open_pull_requests": 9,
            "stale_pull_requests": 3,
            "note": "mock data — set GITHUB_TOKEN, GITHUB_REPO and USE_MOCK_DATA=false for live data",
        }


def _is_stale(updated_at: str | None, days: int = 5) -> bool:
    if not updated_at:
        return False
    from datetime import datetime, timezone

    updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - updated).days >= days


github_client = GitHubClient()
