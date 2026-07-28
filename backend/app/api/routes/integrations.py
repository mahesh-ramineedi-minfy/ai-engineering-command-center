from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.deps import get_current_manager
from app.models.user import User

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/status")
async def status(current_user: User = Depends(get_current_manager)) -> dict:
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
