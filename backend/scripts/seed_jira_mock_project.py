"""
One-off admin script: seed the configured Jira project (JIRA_PROJECT_KEY) with a
realistic-looking mix of issues so the live Jira MCP integration (jira_client.py)
has real sprint data to read back.

Not part of the running app — run manually, once, after completing the manual
setup in backend/docs/jira-setup.md (Jira Cloud site + Scrum project + API token
+ an active sprint already started).

Usage:
    python scripts/seed_jira_mock_project.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.config import settings  # noqa: E402
from app.integrations.jira_mcp import call_tool  # noqa: E402

ISSUES = [
    ("Story", "Add SSO login support"),
    ("Story", "Migrate billing service to new schema"),
    ("Task", "Upgrade CI runners to latest image"),
    ("Task", "Write onboarding docs for new hires"),
    ("Bug", "Fix intermittent timeout on checkout API"),
    ("Bug", "Resolve flaky integration test in payments"),
    ("Story", "Build usage analytics dashboard"),
    ("Task", "Rotate staging environment credentials"),
]

# Indexes (into ISSUES) to transition to Done, to produce a non-trivial completion_pct.
DONE_INDEXES = {0, 2, 4, 5}


async def resolve_active_sprint() -> tuple[str, int]:
    """Find the active sprint's custom-field id and sprint id.

    jira_client.py's JQL relies on `sprint in openSprints()`, but new issues
    created via createJiraIssue land in the backlog by default — they need the
    Sprint field set explicitly to show up. There's no list-sprints MCP tool,
    so this reads the field/sprint id off any issue already in the open sprint
    (Jira's sample "Task 1"/"Task 2" issues, if the runbook's "Start sprint"
    step was followed) rather than hardcoding customfield_10020, which isn't
    guaranteed identical across sites.
    """
    result = await call_tool(
        "searchJiraIssuesUsingJql",
        {"jql": f'project = "{settings.jira_project_key}" AND sprint in openSprints()', "maxResults": 1, "view": "full"},
    )
    issues = result.get("data", {}).get("issues", []) if isinstance(result, dict) else []
    if not issues:
        raise SystemExit(
            "No issues found in an active sprint — start a sprint on the project's Backlog "
            "view first (see backend/docs/jira-setup.md step 6)."
        )
    sprint_field = issues[0]["fields"]["customFields"]["Sprint"]
    return sprint_field["id"], sprint_field["value"][0]["id"]


async def create_issue(issue_type: str, summary: str, sprint_field_id: str, sprint_id: int) -> str:
    result = await call_tool(
        "createJiraIssue",
        {
            "projectKey": settings.jira_project_key,
            "issueType": issue_type,
            "summary": summary,
            "additional_fields": {sprint_field_id: sprint_id},
        },
    )
    key = result.get("data", {}).get("key") if isinstance(result, dict) else None
    if not key:
        raise RuntimeError(f"createJiraIssue returned no issue key: {result!r}")
    return key


async def transition_to_done(issue_key: str) -> None:
    await call_tool("transitionJiraIssue", {"issueIdOrKey": issue_key, "transitionName": "Done"})


async def main() -> None:
    if not (settings.jira_url and settings.jira_email and settings.jira_api_token and settings.jira_project_key):
        raise SystemExit(
            "Missing JIRA_URL / JIRA_EMAIL / JIRA_API_TOKEN / JIRA_PROJECT_KEY in backend/.env — "
            "see backend/docs/jira-setup.md."
        )

    sprint_field_id, sprint_id = await resolve_active_sprint()
    print(f"seeding into sprint {sprint_id} (field {sprint_field_id})")

    created = []
    for i, (issue_type, summary) in enumerate(ISSUES):
        try:
            key = await create_issue(issue_type, summary, sprint_field_id, sprint_id)
        except Exception as exc:
            print(f"FAILED to create '{summary}': {exc}")
            continue
        created.append(key)
        print(f"created {key}: [{issue_type}] {summary}")

        if i in DONE_INDEXES:
            try:
                await transition_to_done(key)
                print(f"  -> transitioned {key} to Done")
            except Exception as exc:
                print(f"  -> FAILED to transition {key} to Done: {exc}")

    print(f"\nSeeded {len(created)}/{len(ISSUES)} issues in project {settings.jira_project_key}.")
    print("Verify with: python -c \"import asyncio; from app.integrations.jira_client import jira_client; "
          "print(asyncio.run(jira_client.fetch_summary()))\"")


if __name__ == "__main__":
    asyncio.run(main())
