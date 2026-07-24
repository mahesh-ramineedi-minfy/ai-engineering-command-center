from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/status")
async def status() -> dict:
    """Connection status per signal source, for the frontend status bar."""
    return {
        "mock_mode": settings.use_mock_data,
        "sources": [
            {"name": "Jira", "key": "jira", "configured": bool(settings.jira_url and settings.jira_api_token)},
            {"name": "GitHub", "key": "github", "configured": bool(settings.github_token and settings.github_repo)},
            {"name": "CI/CD", "key": "cicd", "configured": bool(settings.github_token and settings.github_repo)},
            {"name": "Monitoring", "key": "monitoring", "configured": False},
            {"name": "Incidents", "key": "incidents", "configured": False},
        ],
    }
