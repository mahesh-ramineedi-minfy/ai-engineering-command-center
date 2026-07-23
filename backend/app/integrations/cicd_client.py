import httpx

from app.core.config import settings

GITHUB_API = "https://api.github.com"


class CicdClient:
    """Build and deploy status, sourced from GitHub Actions workflow runs."""

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
            resp = await client.get(f"/repos/{repo}/actions/runs", params={"per_page": 20})
            runs = resp.json().get("workflow_runs", []) if resp.status_code == 200 else []

            total = len(runs)
            failed = len([r for r in runs if r.get("conclusion") == "failure"])
            success = len([r for r in runs if r.get("conclusion") == "success"])

            return {
                "source": "cicd",
                "repo": repo,
                "recent_run_count": total,
                "successful_runs": success,
                "failed_runs": failed,
                "failure_rate_pct": round((failed / total) * 100, 1) if total else 0,
                "last_run_status": runs[0].get("conclusion") if runs else None,
            }

    def _mock(self, repo: str | None) -> dict:
        return {
            "source": "cicd",
            "repo": repo or "acme/delivery-app",
            "recent_run_count": 20,
            "successful_runs": 16,
            "failed_runs": 4,
            "failure_rate_pct": 20.0,
            "last_run_status": "failure",
            "note": "mock data — reuses GITHUB_TOKEN/GITHUB_REPO with USE_MOCK_DATA=false for live GitHub Actions data",
        }


cicd_client = CicdClient()
