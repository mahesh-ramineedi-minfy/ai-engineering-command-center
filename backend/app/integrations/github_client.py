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
                "list_pull_requests", {"owner": owner, "repo": name, "state": "all", "perPage": 50}
            )
        except Exception:
            prs = []

        commits = commits if isinstance(commits, list) else []
        prs = [pr for pr in prs if isinstance(pr, dict)] if isinstance(prs, list) else []

        open_prs = [pr for pr in prs if pr.get("state") == "open"]
        closed_prs = [pr for pr in prs if pr.get("state") == "closed"]
        stale_prs = [pr for pr in open_prs if _is_stale(pr.get("updated_at"))]
        contributors = {c.get("commit", {}).get("author", {}).get("name") for c in commits if isinstance(c, dict)}

        return {
            "source": "github",
            "repo": repo,
            "recent_commit_count": len(commits),
            "active_contributors": len([c for c in contributors if c]),
            "open_pull_requests": len(open_prs),
            "stale_pull_requests": len(stale_prs),
            "closed_pull_requests": len(closed_prs),
            "open_pull_request_list": [_pr_summary(pr) for pr in open_prs[:10]],
            "closed_pull_request_list": [_pr_summary(pr) for pr in closed_prs[:10]],
        }

    def _mock(self, repo: str | None) -> dict:
        return {
            "source": "github",
            "repo": repo or "acme/delivery-app",
            "recent_commit_count": 47,
            "active_contributors": 6,
            "open_pull_requests": 9,
            "stale_pull_requests": 3,
            "closed_pull_requests": 14,
            "open_pull_request_list": [
                {"number": 101, "title": "Add retry backoff to CI/CD polling", "state": "open", "merged": False, "url": "https://github.com/acme/delivery-app/pull/101"},
                {"number": 99, "title": "Fix flaky checkout integration test", "state": "open", "merged": False, "url": "https://github.com/acme/delivery-app/pull/99"},
            ],
            "closed_pull_request_list": [
                {"number": 97, "title": "Bump pgvector image to pg16", "state": "closed", "merged": True, "url": "https://github.com/acme/delivery-app/pull/97"},
                {"number": 95, "title": "Revert delivery-health digest prototype", "state": "closed", "merged": False, "url": "https://github.com/acme/delivery-app/pull/95"},
            ],
            "note": "mock data — set GITHUB_TOKEN, GITHUB_REPO and USE_MOCK_DATA=false for live data",
        }


def _pr_summary(pr: dict) -> dict:
    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "state": pr.get("state"),
        "merged": pr.get("merged", False),
        "url": pr.get("html_url"),
    }


def _is_stale(updated_at: str | None, days: int = 5) -> bool:
    if not updated_at:
        return False
    from datetime import datetime, timezone

    updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - updated).days >= days


github_client = GitHubClient()
