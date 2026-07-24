# AI Engineering Command Center

An agentic engineering operations platform that consolidates sprint progress (Jira), code
activity (GitHub), build/deploy status (CI/CD), uptime (monitoring), and incident history into
a single conversational interface. An orchestrator agent investigates questions by calling
tools across these sources, correlates the results, and returns executive-ready summaries with
recommended actions.

## Stack

- **Backend**: FastAPI, SQLAlchemy (async) + PostgreSQL, NVIDIA NIM (OpenAI-compatible
  tool-use API, default model `moonshotai/kimi-k2.6` with automatic fallback to
  `meta/llama-3.1-70b-instruct` if the primary model call fails)
- **Frontend**: React (Vite)
- **Live data sources**: GitHub and Jira are read through their official remote MCP servers
  (not direct REST calls) — see `backend/app/integrations/github_mcp.py` and `jira_mcp.py`

## Prerequisites

- Python 3.11+
- Node 18+
- Docker (for Postgres via `docker-compose`), or a Postgres instance of your own

## Setup

### 1. Database

```bash
docker compose up -d
```

Starts Postgres on `localhost:5432` and Adminer (DB browser UI) on `localhost:8080`.

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
copy .env.example .env        # Windows; use `cp` on macOS/Linux
```

Edit `.env` and set `NVIDIA_API_KEY` (get one at https://build.nvidia.com/). Leave
`USE_MOCK_DATA=true` to run fully demoable without Jira/GitHub credentials — each integration
client falls back to realistic mock data when it isn't configured.

```bash
uvicorn app.main:app --reload --port 8001
```

API docs at `http://localhost:8001/docs`. (Port 8001 rather than the more typical 8000 — pick
whatever's free on your machine, just keep `frontend/.env`'s `VITE_API_BASE_URL` in sync.)

On Windows, if NVIDIA calls hang indefinitely instead of returning or erroring, it's a known
asyncio/httpx issue with the default `ProactorEventLoop` — already worked around in
`app/main.py` by forcing `WindowsSelectorEventLoopPolicy`, so this should only matter if you're
debugging a similar hang elsewhere.

### 3. Frontend

```bash
cd frontend
npm install
copy .env.example .env        # Windows; use `cp` on macOS/Linux
npm run dev
```

App at `http://localhost:5173`.

## Going live with real data

Each integration client in `backend/app/integrations/` checks for credentials and falls back
to mock data if they're missing:

- **GitHub / CI/CD**: set `GITHUB_TOKEN` and `GITHUB_REPO`, then `USE_MOCK_DATA=false`. Both are
  read through GitHub's remote MCP server (`https://api.githubcopilot.com/mcp/`) — CI/CD status
  specifically via its consolidated `actions_list` tool, since there's no separate `CICD_*`
  config; it reuses the GitHub credentials against the same repo's Actions data.
- **Jira**: set `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`, then
  `USE_MOCK_DATA=false`. Read through Atlassian's remote MCP server. This one needs real
  one-time setup beyond just an API token — a scoped "Rovo MCP V2" token, an org-admin toggle,
  and (if you want live-data testing) a project with an active sprint — see
  **`backend/docs/jira-setup.md`** for the full walkthrough.
- **Monitoring / Incidents**: no universal vendor API exists, so these always return mock data.
  Wire in a real provider (Datadog, Grafana, PagerDuty, ...) in
  `backend/app/integrations/monitoring_client.py`.

## Chat guardrails

`POST /api/chat` rejects empty/oversized messages (max 4000 chars) with a 422, and rate-limits
each client IP to `CHAT_RATE_LIMIT_PER_MINUTE` requests/minute (default 20, 0 disables) with a
429 + `Retry-After`. The orchestrator's system prompt also instructs the model to treat tool
output as data (never as instructions) and to decline off-topic or instruction-override requests
— see the "Guardrails on `POST /api/chat`" note in `CLAUDE.md` for details.

## Extending the agent

The orchestrator (`backend/app/agents/orchestrator.py`) is a single tool-use loop with
five tools defined in `backend/app/agents/tools.py`, one per signal source. To add a new
signal:

1. Add a client in `backend/app/integrations/` with an async `fetch_summary()` method.
2. Register a tool schema + dispatch entry in `backend/app/agents/tools.py`.

No changes to the orchestrator loop or API routes are needed.
