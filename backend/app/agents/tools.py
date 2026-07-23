"""
Tool definitions for the orchestrator agent, and the dispatch table that
executes them. Each tool maps 1:1 to a specialized integration client — add
a new signal source by adding a client (see app/integrations/) and
registering it here.

Tools take no parameters: this app monitors a single configured repo/
project/service (set via env vars in app/core/config.py), not an arbitrary
target the model picks per call. Earlier versions exposed an optional
repo/project_key/service argument, but weaker models filled it with a
plausible-looking hallucinated value instead of leaving it empty, silently
shadowing the real configured target. Removing the parameter removes the
hallucination surface entirely.
"""

from app.integrations.cicd_client import cicd_client
from app.integrations.github_client import github_client
from app.integrations.jira_client import jira_client
from app.integrations.monitoring_client import incident_client, monitoring_client

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_sprint_status",
            "description": "Get current sprint progress from Jira: completion %, blocked issues, days remaining.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_code_activity",
            "description": "Get recent code activity from GitHub: commit volume, active contributors, open and stale pull requests.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_build_status",
            "description": "Get build and deploy status from CI/CD: recent run outcomes and failure rate.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_uptime",
            "description": "Get service uptime and current operational status from monitoring.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_incident_history",
            "description": "Get recent incident history for a service: severity, duration, root cause.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

_DISPATCH = {
    "get_sprint_status": lambda: jira_client.fetch_summary(),
    "get_code_activity": lambda: github_client.fetch_summary(),
    "get_build_status": lambda: cicd_client.fetch_summary(),
    "get_uptime": lambda: monitoring_client.fetch_summary(),
    "get_incident_history": lambda: incident_client.fetch_summary(),
}


async def run_tool(name: str, tool_input: dict) -> dict:
    handler = _DISPATCH.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    return await handler()
