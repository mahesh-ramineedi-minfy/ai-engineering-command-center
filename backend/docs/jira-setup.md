# Setting up a mock Jira Cloud project for live testing

`jira_client.py` reads sprint data through Atlassian's remote MCP server, the same way
`github_client.py` reads through GitHub's. Testing it live needs a real Jira Cloud site — there's
no anonymous/mock server to point at. This covers standing up a disposable test site and getting
the auth right, which took several rounds of trial and error to nail down (see the Jira paragraph
in the root `CLAUDE.md` for the technical reasons behind each step below).

## 1. Create a free Jira Cloud site

Go to https://www.atlassian.com/software/jira/free and sign up (or sign in if you already have
an Atlassian account). Note the site URL you're given, e.g. `https://your-name.atlassian.net` —
this is `JIRA_URL`.

## 2. Create a Scrum project

Create a project using the **Scrum** template (not Kanban — the existing JQL relies on
`sprint in openSprints()`, and Kanban boards have no sprints). Whatever key Jira assigns (e.g.
`SCRUM`) is `JIRA_PROJECT_KEY`.

## 3. Enable API token authentication for the Rovo MCP server (org admin)

Go to **admin.atlassian.com → Rovo → Rovo MCP server → Authentication** and enable API token
authentication. Without this, every MCP call fails with "You don't have permission to connect
via API token." If you signed up for the site yourself, you're the org admin.

## 4. Create a scoped API token

Go to https://id.atlassian.com/manage-profile/security/api-tokens and click **"Create API token
with scopes"** (not the plain "Create API token" — that creates a legacy/classic token, which
fails with "Teamwork Graph tools require a modern API token"). Pick **"Rovo MCP V2"** as the app,
and select every scope checkbox offered — the tools used here (`searchJiraIssuesUsingJql`,
`createJiraIssue`, `transitionJiraIssue`, `editJiraIssue`) each need their own scope, and there's
no single "grant everything" option. This is `JIRA_API_TOKEN`; `JIRA_EMAIL` is the email of the
account you signed up with.

## 5. Fill in `backend/.env`

```
JIRA_URL=https://your-name.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=<the scoped token from step 4>
JIRA_PROJECT_KEY=SCRUM
USE_MOCK_DATA=false
```

## 6. Start a sprint

Open the project's **Backlog** view and click **Start sprint**. Without an active sprint,
`sprint in openSprints()` matches nothing and `jira_client.fetch_summary()` will correctly (if
unhelpfully) report zero issues. There's no MCP tool for this — Atlassian's toolset has no
board/sprint-management tools — it has to be done in the Jira UI.

## 7. Seed some issues

```bash
cd backend
python scripts/seed_jira_mock_project.py
```

This creates ~8 issues in the project, assigns them to the active sprint (new issues land in the
backlog by default — the script discovers the sprint's field/id off an issue already in the
sprint, e.g. Jira's own sample "Task 1"/"Task 2"), and moves a few to Done. `blocked_issues` stays
at 0 — Jira's default workflow has no "Blocked" status, and `jira_client.py` flags blocked issues
by status name (`"blocked" in status.name.lower()`); a 0 is still a valid, honest result to
verify against.

If a tool call fails with an unfamiliar error, run:

```bash
python scripts/jira_mcp_list_tools.py <toolName>
```

against your real credentials to see its actual `inputSchema`, the same way `actions_list`'s
schema was checked for the GitHub CI/CD integration.

## 8. Verify

```bash
python -c "import asyncio; from app.integrations.jira_client import jira_client; print(asyncio.run(jira_client.fetch_summary()))"
curl http://localhost:8001/api/integrations/status
```

`jira` should report real numbers matching what the seed script created, and `configured: true`
in the status endpoint.
