import httpx

from app.core.config import settings


class JiraClient:
    """Sprint progress: committed vs. completed points, blockers, days remaining."""

    def _configured(self) -> bool:
        return bool(settings.jira_url and settings.jira_email and settings.jira_api_token)

    async def fetch_summary(self, project_key: str | None = None) -> dict:
        project_key = project_key or settings.jira_project_key
        if not settings.use_mock_data and self._configured():
            return await self._fetch_live(project_key)
        return self._mock(project_key)

    async def _fetch_live(self, project_key: str) -> dict:
        auth = (settings.jira_email, settings.jira_api_token)
        jql = f'project = "{project_key}" AND sprint in openSprints()'
        async with httpx.AsyncClient(base_url=settings.jira_url, auth=auth, timeout=15) as client:
            resp = await client.get("/rest/api/3/search", params={"jql": jql, "maxResults": 100})
            issues = resp.json().get("issues", []) if resp.status_code == 200 else []

            done = [i for i in issues if i["fields"]["status"]["statusCategory"]["key"] == "done"]
            blocked = [i for i in issues if "blocked" in i["fields"]["status"]["name"].lower()]

            return {
                "source": "jira",
                "project_key": project_key,
                "total_issues": len(issues),
                "completed_issues": len(done),
                "blocked_issues": len(blocked),
                "completion_pct": round((len(done) / len(issues)) * 100, 1) if issues else 0,
            }

    def _mock(self, project_key: str | None) -> dict:
        return {
            "source": "jira",
            "project_key": project_key or "DEL",
            "sprint_name": "Sprint 24",
            "total_issues": 32,
            "completed_issues": 18,
            "blocked_issues": 4,
            "completion_pct": 56.3,
            "days_remaining": 3,
            "note": "mock data — set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN and USE_MOCK_DATA=false for live data",
        }


jira_client = JiraClient()
