"""
Uptime and incident history.

No universal REST API exists across monitoring vendors (Datadog, Grafana,
PagerDuty, etc.), so this client always returns mock data. To go live, add
vendor-specific auth to Settings and branch here the same way
GitHubClient/JiraClient do.
"""


class MonitoringClient:
    async def fetch_summary(self, service: str | None = None) -> dict:
        return {
            "source": "monitoring",
            "service": service or "delivery-app-api",
            "uptime_pct_30d": 99.82,
            "current_status": "degraded",
            "active_incidents": 1,
            "note": "mock data — wire in a real provider (Datadog/Grafana/PagerDuty) in monitoring_client.py",
        }


class IncidentClient:
    async def fetch_summary(self, service: str | None = None) -> dict:
        return {
            "source": "incidents",
            "service": service or "delivery-app-api",
            "incidents_last_30d": 3,
            "recent_incidents": [
                {"id": "INC-142", "severity": "high", "duration_minutes": 47, "cause": "database connection pool exhaustion"},
                {"id": "INC-139", "severity": "medium", "duration_minutes": 12, "cause": "bad deploy, rolled back"},
                {"id": "INC-131", "severity": "low", "duration_minutes": 5, "cause": "third-party API rate limit"},
            ],
            "note": "mock data — wire in a real incident/PagerDuty provider in monitoring_client.py",
        }


monitoring_client = MonitoringClient()
incident_client = IncidentClient()
