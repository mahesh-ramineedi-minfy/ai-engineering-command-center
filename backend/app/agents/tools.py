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

search_error_logs is the one deliberate exception, taking a required `query`
string. The zero-params rule is about not letting the model pick a *target*
(repo/project/service) — this app only ever monitors one configured target,
so any value there is necessarily wrong. A search query isn't a target: it's
the actual point of a RAG tool, and a slightly-off query just returns
slightly-off (not silently-wrong) results, so the original failure mode
doesn't apply.
"""

from app.integrations.cicd_client import cicd_client
from app.integrations.github_client import github_client
from app.integrations.jira_client import jira_client
from app.integrations.log_search_client import log_search_client
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
    {
        "type": "function",
        "function": {
            "name": "search_error_logs",
            "description": (
                "Semantically search CI/CD build logs and application (CloudWatch-style) logs for "
                "the actual error/stack-trace evidence behind a bug or incident — use this when a "
                "question is about a specific error or root cause, not just aggregate build/uptime "
                "stats. Returns the matching log lines, not a summary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for, e.g. 'database connection pool exhaustion' or 'checkout deploy failure'.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]

_DISPATCH = {
    # **_ ignores any stray params a model might hallucinate onto a
    # zero-param tool — run_tool always calls handlers with **tool_input, and
    # these five have nothing to accept.
    "get_sprint_status": lambda **_: jira_client.fetch_summary(),
    "get_code_activity": lambda **_: github_client.fetch_summary(),
    "get_build_status": lambda **_: cicd_client.fetch_summary(),
    "get_uptime": lambda **_: monitoring_client.fetch_summary(),
    "get_incident_history": lambda **_: incident_client.fetch_summary(),
    "search_error_logs": lambda query: log_search_client.search(query),
}


async def run_tool(name: str, tool_input: dict) -> dict:
    handler = _DISPATCH.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return await handler(**tool_input)
    except TypeError as exc:
        # e.g. search_error_logs called without its required `query` arg —
        # surface as a tool result the model can react to, not a crashed request.
        return {"error": f"invalid arguments for {name}: {exc}"}
