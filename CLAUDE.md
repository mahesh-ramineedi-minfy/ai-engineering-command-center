# CLAUDE.md

This file provides  guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AI Engineering Command Center — an agentic engineering operations platform. It consolidates sprint
progress (Jira), code activity (GitHub), build/deploy status (CI/CD), uptime (monitoring),
incident history, and semantic search over CI/CD + application logs into one conversational
interface. A tool-use agent (NVIDIA NIM, default model `moonshotai/kimi-k2.6`, falling back to
`meta/llama-3.1-70b-instruct` if that call fails) investigates questions, correlates signals
across systems, and returns executive-ready summaries with recommended actions (backlog
reprioritization, resourcing, escalation).

## Commands

### Backend (`backend/`)

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001            # run dev server (http://localhost:8001/docs for API docs)
```

No test suite or linter is configured yet. Two project-scoped Claude Code skills are available
under `.claude/skills/` (pulled from anthropics/skills, unmodified): **`mcp-builder`** — guidance
for building/reviewing MCP servers and clients, directly relevant to `github_mcp.py`/`jira_mcp.py`
and any future signal-source integration — and **`webapp-testing`** — a Playwright-based toolkit
for exercising the frontend, relevant given there's no test suite yet. Neither runs automatically;
invoke them (`/mcp-builder`, `/webapp-testing`) when doing MCP or frontend-testing work.

### Frontend (`frontend/`)

```bash
npm install
npm run dev        # dev server on http://localhost:5173
npm run build
```

### Database

```bash
docker compose up -d   # Postgres (pgvector-enabled) on :5432, Adminer (DB browser) on :8080
```

Tables are created automatically on backend startup via `SQLAlchemy Base.metadata.create_all`
(see `app/core/database.py`), which also runs `CREATE EXTENSION IF NOT EXISTS vector` first —
there is no Alembic/migration setup.

### Environment

Both `backend/.env.example` and `frontend/.env.example` list required env vars — copy each to
`.env` in its own directory. Key backend var: `NVIDIA_API_KEY` (from https://build.nvidia.com/).
`USE_MOCK_DATA=true` (default) makes the whole app demoable with zero third-party credentials.

## Architecture

**One orchestrator agent, five tools, one loop.** `app/agents/orchestrator.py` runs a single
OpenAI-compatible tool-use loop against NVIDIA NIM (`run_agent`, max 8 iterations) rather than
separate agent processes per domain. The system prompt instructs the model to call multiple
tools when a question spans systems and explicitly correlate findings (e.g. failed builds +
open incident + blocked sprint issue = one risk story) but to keep single-system questions to
one tool call — earlier versions over-called all five tools even for narrow questions until the
prompt explicitly said not to. Tool schemas and the dispatch table live in
`app/agents/tools.py` — each tool maps 1:1 to an integration client.

**`NVIDIA_MODEL` (`moonshotai/kimi-k2.6`) rejects more than one `tool_call` per response** — a
`400 BadRequestError` ("This model only supports single tool-calls at once!") if it ever tries to
batch multiple tool calls into one turn, which is exactly what the system prompt above invites it
to do for a broad "release risk"/"delivery health" question needing several signals.
`run_agent`'s two `chat.completions.create` calls both pass `parallel_tool_calls=False` to force
one tool call per turn — don't drop it, and don't assume a switch away from `kimi-k2.6` makes it
safe to drop either without confirming the replacement model actually supports parallel calls.
This surfaced live while prototyping a (since-reverted) delivery-health digest that needed all 5
direct tools in one investigation; `chat.py`'s broad `except openai.APIError` had been silently
converting it to a generic "temporarily unavailable" 502 with no logged traceback, so it read as
unexplained flakiness until reproduced by calling `run_agent` directly in a script. `MAX_TOOL_ITERATIONS`
is 8 (not the more obvious 6) specifically because a broad question now costs one iteration per
signal instead of being able to batch them — 5 tools + 1 synthesis turn is already 6, with no
margin.

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

**`run_agent` falls back to `NVIDIA_FALLBACK_MODEL`** (default `meta/llama-3.1-70b-instruct`) if
a chat-completion call raises `openai.APIError`, and sticks with the fallback for the rest of
that run rather than retrying the primary model every iteration. This exists because NIM model
access is per-model/per-account — `moonshotai/kimi-k2.6` (the default `NVIDIA_MODEL`) needs
separate approval even when catalog-listed, so a fresh account can fail on the primary model
specifically, not NIM as a whole. If the fallback also fails, the exception still propagates to
`chat.py`'s `RateLimitError`/`APITimeoutError`/`APIError` handling — this doesn't swallow errors,
it just gets one more model to try first.

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

**Jira data also comes from a remote MCP server**, Atlassian's, via `app/integrations/jira_mcp.py`.
Several things about it are non-obvious and were only discoverable by testing against a real
account — don't "fix" them back to the more obvious-looking alternative:

- **URL must be `https://mcp.atlassian.com/v1/mcp/preview`, not `.../v1/mcp`.** The plain `/v1/mcp`
  endpoint only exposes 3 generic `getTeamworkGraphContext`/`getTeamworkGraphObject`/
  `addTeamworkGraphContext` tools for API-token auth — no Jira-specific tools at all. `/preview`
  has the full Jira toolset (`searchJiraIssuesUsingJql`, `createJiraIssue`, `transitionJiraIssue`,
  etc.), despite the name suggesting it's the less-stable one.
- **Auth is HTTP Basic** (`base64(JIRA_EMAIL:JIRA_API_TOKEN)`), not a bearer token like GitHub's.
  The token must be a **scoped API token** created via "Create API token with scopes" →
  **"Rovo MCP V2"** at id.atlassian.com/manage-profile/security/api-tokens, with every scope
  checkbox under that app selected. Classic/legacy API tokens fail outright ("Teamwork Graph
  tools require a modern API token"); the org's admin also has to enable API token auth once, at
  admin.atlassian.com → Rovo → Rovo MCP server → Authentication.
- **cloudId is resolved via Atlassian's public `{JIRA_URL}/_edge/tenant_info` endpoint**, not the
  `getAccessibleAtlassianResources` MCP tool. That tool needs `read:me`/`read:account` scopes that
  live outside the "Rovo MCP V2" token category entirely — no combination of scopes on that
  category can satisfy it, so it's a dead end, not a missing checkbox. `tenant_info` needs no auth
  and this app only ever targets one fixed `JIRA_URL` anyway, so the result is cached per process
  (`jira_mcp._cloud_id_cache`).
- **`searchJiraIssuesUsingJql` needs `view: "full"`.** The default `view: "compact"` omits
  `fields.status.statusCategory`, which `jira_client.py` depends on to classify issues as done.
  Responses are also wrapped in `{"data": {...}}`, not returned at the top level — unwrap
  `result["data"]["issues"]`, not `result["issues"]`.
- **New issues don't land in the active sprint automatically.** `createJiraIssue` puts them in the
  backlog; `sprint in openSprints()` (the JQL `jira_client.py` uses) won't match them until the
  Sprint field is set explicitly via `additional_fields: {<sprint_field_id>: <sprint_id>}` on
  create or through `editJiraIssue`. There's no list-sprints MCP tool, so
  `scripts/seed_jira_mock_project.py` discovers the field id and active sprint id by reading them
  off any issue already in an open sprint, rather than hardcoding `customfield_10020`.

`backend/docs/jira-setup.md` covers standing up a disposable Jira Cloud site to test against, and
`backend/scripts/jira_mcp_list_tools.py` prints a live tool's real `inputSchema` — useful the same
way discovering `actions_list`'s real schema was on the GitHub side, if Atlassian's tool surface
shifts again.

**`search_error_logs` is a RAG pipeline over a mock log corpus** (`app/rag/`), the sixth
orchestrator tool and the only one taking a parameter. `app/rag/mock_logs.py` is a static,
hand-authored list of 30 CI/CD build logs and CloudWatch-style application logs (`source`:
`"cicd"`/`"cloudwatch"`) — a few deliberately echo `monitoring_client.py`'s mock incidents
(INC-142, INC-139, INC-131) so a question about one has a concrete log line to retrieve, not just
the incident summary. `app/rag/embeddings.py` embeds via NVIDIA NIM's `/v1/embeddings`
(`nvidia/nv-embedqa-e5-v5`, 1024-dim) — **not** `baai/bge-m3`, which is catalog-listed and passes
`client.models.list()` but 500s on every embeddings call on this account; same class of gotcha as
`NVIDIA_MODEL`'s `kimi-k2.6` approval gate, just discovered live instead of assumed. `nv-embedqa`
is an *asymmetric* model — `embed()` takes a required `input_type: "query" | "passage"`, calling
it wrong doesn't error, it just quietly returns worse-matched results, so ingestion always passes
`"passage"` and `search_logs()` always passes `"query"`. `app/rag/ingest.py`'s
`ensure_logs_indexed()` runs once from `main.py`'s `lifespan` (idempotent — checks `LogChunk` row
count first) and is skipped entirely without `NVIDIA_API_KEY`, so the app still boots fully
demoable with zero credentials; `search_error_logs` just returns no results in that case rather
than crashing startup. Storage is pgvector (`app/models/log_chunk.py`), which is why
`docker-compose.yml`'s Postgres image is `pgvector/pgvector:pg16` rather than `postgres:16-alpine`
and `database.py`'s `init_db()` runs `CREATE EXTENSION IF NOT EXISTS vector` before
`create_all` — swapped in place on the existing data volume with no migration needed, since
Postgres data files aren't tied to the base image's libc.

Because it's the one parameterized tool, `run_tool()` in `tools.py` calls handlers with
`**tool_input` instead of no args — the five zero-param handlers take `**_` specifically so a
model hallucinating a stray argument onto one of *them* doesn't raise, preserving the original
"tools take zero parameters" guarantee. A `TypeError` from a handler (e.g. `search_error_logs`
called without its required `query`) is caught in `run_tool()` and returned as an error dict the
model can react to, rather than propagating up and crashing the chat request.

**Chat flow**: `POST /api/chat` (`app/api/routes/chat.py`) loads or creates a `Conversation`,
converts its `Message` history to OpenAI-style chat message format, calls `run_agent`, then persists
both the user message and assistant reply. The response includes a `tool_calls` trace (which
tools fired and a one-line summary of each result) so the frontend can show what the agent
investigated — rendered as chips under each assistant message in
`frontend/src/components/Chat/MessageBubble.jsx`.

**Guardrails on `POST /api/chat`**: `ChatRequest.message` (`app/schemas/chat.py`) rejects
empty/whitespace-only and >4000-char messages with a 422 before `run_agent` is ever called.
`app/core/rate_limit.py`'s `rate_limit_chat` dependency caps requests per client IP at
`CHAT_RATE_LIMIT_PER_MINUTE` (default 20/min) with a 429 + `Retry-After` header — it's an
in-memory sliding window, single-process only, meant to stop one client/retry-loop from burning
NVIDIA quota, not a security boundary; swap for a shared store before running multiple workers.
The orchestrator's `SYSTEM_PROMPT` also explicitly instructs the model to treat tool output
(commit messages, issue titles, incident descriptions — all third-party-writable text that flows
back in as `tool` role messages) as data, never as instructions, and to decline off-topic or
instruction-override ("ignore your previous instructions...") requests rather than comply —
verified live against a jailbreak-style prompt.

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
