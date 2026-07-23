from app.core.config import settings
from app.integrations.github_mcp import call_tool


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
        owner, name = repo.split("/", 1)

        try:
            commits = await call_tool("list_commits", {"owner": owner, "repo": name, "perPage": 20})
        except Exception:
            commits = []
        try:
            prs = await call_tool(
                "list_pull_requests", {"owner": owner, "repo": name, "state": "open", "perPage": 50}
            )
        except Exception:
            prs = []

        commits = commits if isinstance(commits, list) else []
        prs = prs if isinstance(prs, list) else []

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
