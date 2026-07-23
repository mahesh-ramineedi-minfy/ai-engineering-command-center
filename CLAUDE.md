# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AI Engineering Command Center — an agentic engineering operations platform. It consolidates sprint
progress (Jira), code activity (GitHub), build/deploy status (CI/CD), uptime (monitoring), and
incident history into one conversational interface. A tool-use agent (NVIDIA NIM, default
model `meta/llama-3.1-70b-instruct`) investigates questions, correlates signals across systems,
and returns executive-ready summaries with recommended actions (backlog reprioritization,
resourcing, escalation).

## Commands

### Backend (`backend/`)

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001            # run dev server (http://localhost:8001/docs for API docs)
```

No test suite or linter is configured yet.

### Frontend (`frontend/`)

```bash
npm install
npm run dev        # dev server on http://localhost:5173
npm run build
```

### Database

```bash
docker compose up -d   # Postgres on :5432, Adminer (DB browser) on :8080
```

Tables are created automatically on backend startup via `SQLAlchemy Base.metadata.create_all`
(see `app/core/database.py`) — there is no Alembic/migration setup.

### Environment

Both `backend/.env.example` and `frontend/.env.example` list required env vars — copy each to
`.env` in its own directory. Key backend var: `NVIDIA_API_KEY` (from https://build.nvidia.com/).
`USE_MOCK_DATA=true` (default) makes the whole app demoable with zero third-party credentials.

## Architecture

**One orchestrator agent, five tools, one loop.** `app/agents/orchestrator.py` runs a single
OpenAI-compatible tool-use loop against NVIDIA NIM (`run_agent`, max 6 iterations) rather than
separate agent processes per domain. The system prompt instructs the model to call multiple
tools when a question spans systems and explicitly correlate findings (e.g. failed builds +
open incident + blocked sprint issue = one risk story) but to keep single-system questions to
one tool call — earlier versions over-called all five tools even for narrow questions until the
prompt explicitly said not to. Tool schemas and the dispatch table live in
`app/agents/tools.py` — each tool maps 1:1 to an integration client.

**Tools take zero parameters, by design.** This app monitors one configured repo/project/service
at a time (env-var driven), not an arbitrary target the model picks per call. An earlier version
exposed an optional `repo`/`project_key`/`service` argument on each tool; the model (a smaller
NVIDIA-hosted one) would fill it with a plausible-looking hallucinated value instead of leaving
it empty, silently shadowing the real configured target and returning wrong data with no error.
Don't reintroduce a target parameter without also handling that failure mode.

**NVIDIA client config is deliberately defensive** (`app/agents/orchestrator.py`): `timeout=20.0`,
`max_retries=1`, and connection pooling disabled (`max_keepalive_connections=0`). The OpenAI
SDK's defaults (600s timeout, 2 retries) turned a rate-limited or stalled call into what looked
like an indefinite hang; pooled keep-alive connections to this host also intermittently went
silent mid-request. `app/api/routes/chat.py` catches `openai.RateLimitError` /
`APITimeoutError` / `APIError` around the `run_agent` call and returns a clean 503/504/502 with
a human-readable `detail` instead of a bare 500.

**Integration clients follow a strict pattern** (`app/integrations/*.py`): every client exposes
a single async `fetch_summary(**kwargs) -> dict`. Each checks whether real credentials are
configured (via `app/core/config.Settings`) and `USE_MOCK_DATA` is false; if not, it returns
realistic mock data with a `"note"` field explaining what to configure for live data. This
means the whole app — API, agent loop, UI — works end-to-end with zero external credentials.
`monitoring_client.py` (uptime + incidents) always returns mock data since no universal vendor
API exists; wire in a real provider there when needed.

**To add a new signal source**: add a client in `app/integrations/` with `fetch_summary()`,
then register a tool schema + one-line dispatch entry in `app/agents/tools.py`. No changes
needed to the orchestrator loop, API routes, or frontend.

**CI/CD reuses the GitHub client's credentials** (`app/integrations/cicd_client.py` hits the
same repo's GitHub Actions data) rather than being a separate configured source — there's no
separate `CICD_*` env var.

**GitHub and CI/CD data comes from GitHub's remote MCP server, not the REST API directly.**
`app/integrations/github_mcp.py` opens a fresh MCP `ClientSession` per call over streamable
HTTP to `https://api.githubcopilot.com/mcp/`, authenticated with `GITHUB_TOKEN` as a bearer
token and scoped via the `X-MCP-Toolsets: repos,pull_requests,actions` header. `github_client.py`
calls the atomic `list_commits` / `list_pull_requests` tools (camelCase args: `perPage`).
`cicd_client.py` calls the consolidated `actions_list` tool with `method: "list_workflow_runs"`
(snake_case args: `per_page`) — GitHub's Actions toolset exposes one multi-method tool
(`actions_list`/`actions_get`/`actions_run_trigger`/`get_job_logs`) rather than one tool per
REST endpoint; there is no standalone `list_workflow_runs` tool, and calling it directly 404s
with `unknown tool`. Both wrap each `call_tool` in a `try/except` that falls back to an empty
result, mirroring the old non-200-status handling — an MCP call failing shouldn't crash
`fetch_summary`, only zero out that source. Because of that fallback, a wrong tool name or
schema silently degrades to a plausible-looking all-zero result instead of erroring — verify any
new tool call directly (`session.call_tool(...)`, check `isError`) before trusting it just
because `fetch_summary` returned cleanly. This requires `mcp` (the Python MCP SDK), which
pins `starlette==0.38.6` in `requirements.txt`; a bare `pip install mcp` pulls in a newer
starlette that's incompatible with this project's pinned `fastapi==0.115.0` (`starlette<0.39`)
— don't drop that pin without also bumping fastapi.

**Chat flow**: `POST /api/chat` (`app/api/routes/chat.py`) loads or creates a `Conversation`,
converts its `Message` history to OpenAI-style chat message format, calls `run_agent`, then persists
both the user message and assistant reply. The response includes a `tool_calls` trace (which
tools fired and a one-line summary of each result) so the frontend can show what the agent
investigated — rendered as chips under each assistant message in
`frontend/src/components/Chat/MessageBubble.jsx`.

**Don't access `Conversation.messages` as a bare relationship attribute** outside an eager-loaded
query — with `AsyncSession`, that raises `sqlalchemy.exc.MissingGreenlet` even though the same
code looks fine synchronously. `chat.py` explicitly queries `Message` for the existing-conversation
path and uses `selectinload(Conversation.messages)` in the GET routes instead of relying on lazy
relationship access.

**Windows dev only**: the default `ProactorEventLoop` hangs on some async TLS reads via
httpx/anyio (used by the `openai` client) — `app/main.py` forces
`asyncio.WindowsSelectorEventLoopPolicy()` on `sys.platform == "win32"` to work around it. If
NVIDIA calls start hanging again after touching `main.py`, check this is still in place first.

**Frontend** is a single-page chat UI (no router). `StatusBar` polls
`GET /api/integrations/status` on mount to show which sources are live vs. mock-backed.
`ChatWindow` owns conversation state and message list; `conversation_id` from the first
response is threaded into subsequent requests to keep server-side history.
