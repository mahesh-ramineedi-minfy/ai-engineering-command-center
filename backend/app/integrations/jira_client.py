from app.core.config import settings
from app.integrations.jira_mcp import call_tool


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
        jql = f'project = "{project_key}" AND sprint in openSprints()'

        try:
            result = await call_tool("searchJiraIssuesUsingJql", {"jql": jql, "maxResults": 100, "view": "full"})
        except Exception as exc:
            # Don't silently present a fabricated "0 issues" as ground truth — a failed
            # live fetch (e.g. an Atlassian API token missing required scopes) previously
            # looked identical to a genuinely empty sprint. Surface it via `note` instead.
            return {
                "source": "jira",
                "project_key": project_key,
                "total_issues": 0,
                "completed_issues": 0,
                "blocked_issues": 0,
                "completion_pct": 0,
                "issues": [],
                "note": f"live Jira fetch failed, showing no data rather than guessing: {exc}",
            }

        issues = result.get("data", {}).get("issues", []) if isinstance(result, dict) else []
        issues = issues if isinstance(issues, list) else []

        done = [i for i in issues if i["fields"]["status"]["statusCategory"]["key"] == "done"]
        blocked = [i for i in issues if "blocked" in i["fields"]["status"]["name"].lower()]

        return {
            "source": "jira",
            "project_key": project_key,
            "total_issues": len(issues),
            "completed_issues": len(done),
            "blocked_issues": len(blocked),
            "completion_pct": round((len(done) / len(issues)) * 100, 1) if issues else 0,
            "issues": [
                {
                    "key": i.get("key"),
                    "title": i.get("fields", {}).get("summary"),
                    "status": i.get("fields", {}).get("status", {}).get("name"),
                }
                for i in issues
            ],
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
            "issues": [
                {"key": "DEL-101", "title": "Add refresh-token rotation to auth middleware", "status": "Done"},
                {"key": "DEL-104", "title": "Fix pagination bug in commit activity widget", "status": "Done"},
                {"key": "DEL-110", "title": "Migrate incident feed to websocket push", "status": "In Progress"},
                {"key": "DEL-112", "title": "Add pgvector index for log search", "status": "In Progress"},
                {"key": "DEL-115", "title": "Investigate flaky CI job on build runner 3", "status": "Blocked"},
                {"key": "DEL-118", "title": "Write RAG ingestion smoke test", "status": "To Do"},
            ],
            "note": "mock data (showing 6 of 32 issues) — set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN and USE_MOCK_DATA=false for live data",
        }


jira_client = JiraClient()
