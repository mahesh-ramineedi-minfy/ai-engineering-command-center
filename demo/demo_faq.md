# AI Engineering Command Center — Demo FAQ (for reference, not for slides)

Likely judge/audience questions, grounded in actual decisions made in this codebase — not
speculative answers. Organized so you can scan by topic during Q&A.

> The condensed version of this FAQ is now embedded as speaker notes on the **Roadmap slide**
> (slide 9) of `AI_Engineering_Command_Center_Demo.pptx`, right where Q&A naturally follows in
> the deck. That section is reproduced verbatim below so this doc and the deck stay in sync.

## Speaker notes on the Roadmap slide (verbatim)

Show this is a foundation, not a finished product, without undercutting what's already working.
Monitoring is the one source that's always mock (no universal vendor API exists) — that's the
most obvious next real-data integration. The "more signal sources" point is a good chance to
reinforce the extensibility story: adding a new source is a 2-step add (client + tool
registration), no orchestrator changes needed.

**Q&A prep — likely questions and grounded answers, by topic:**

**Product:** Different from just checking dashboards? Dashboards show per-system numbers; this
agent correlates across them (failed build + open incident + blocked sprint issue = one risk
story with a recommended action).

**Architecture:** Why one orchestrator, not multiple agents? Simpler failure modes, one place to
reason about tool choice, no inter-agent coordination needed for a single-user chat loop. Why one
tool call per turn? Default model (kimi-k2.6) hard-rejects batched `tool_calls` with a 400;
`parallel_tool_calls=False` forces one per turn; `MAX_TOOL_ITERATIONS=8` covers 5 tools + 1
synthesis turn with margin. Why zero-param tools? An earlier version let the model pick a target
repo/project per call and a smaller model hallucinated plausible-but-wrong values — removing the
parameter removed the failure mode. Why GitHub/Jira via remote MCP not REST? Standardized tool
surface instead of hand-rolling auth/parsing per vendor. What if NIM is down/rate-limited?
`timeout=20s`, `max_retries=1`, no pooling, clean 502/503/504 instead of a hang; automatic
fallback to `meta/llama-3.1-70b-instruct` mid-run if the primary model fails. Why pgvector?
Reuses the same Postgres instance already used for app data, no extra infra.

**Security:** Prompt injection via tool output (e.g. malicious commit message)? System prompt
treats tool output as data, never instructions, verified live against a jailbreak-style prompt.
Chat guardrails? 422 on empty/>4000-char messages, per-IP rate limit (20/min default, 429 +
`Retry-After`, in-memory — abuse mitigation not a security boundary). Auth? JWT access token +
httponly refresh cookie; refresh-token reuse revokes all sessions for that user (theft-detection
pattern). Zero-credential demo? Yes — `USE_MOCK_DATA=true` by default, every integration falls
back to realistic mock data; monitoring/incidents always mock, log search always the mock corpus
by design.

**Not production-ready yet (be upfront if asked):** in-memory rate limiter (single-process
only), monitoring/incidents mock-only, no multi-tenant scoping, no migration tooling
(`create_all`, no Alembic).

**Demo fallback:** if live demo breaks, slide 4's screenshot is real (not a mockup), and slide 8
narrates the traced "why did the checkout deploy fail?" example step by step without needing the
live app.

## Full FAQ, by topic

## Product / positioning

**Q: What problem does this actually solve?**
Engineering signal is scattered across Jira, GitHub, CI/CD, uptime monitoring, incidents, and
logs. Answering "is this release healthy?" today means manually opening 5+ tools and
cross-referencing them by hand. This gives you one conversational interface that does that
correlation for you.

**Q: Who's the target user?**
An engineering manager or tech lead doing release/delivery-health triage — the persona the demo
account (`manager@example.com`) is modeled on.

**Q: How is this different from just checking dashboards in each tool?**
Dashboards show you numbers per-system. This agent *correlates* — e.g. a failed build + an open
incident + a blocked sprint issue becomes one risk story with a recommended action, not three
things you have to notice are related yourself.

## Architecture

**Q: Why one orchestrator agent instead of multiple specialized agents?**
Simpler failure modes and one place to reason about tool choice, for what's fundamentally a
single-user chat loop — no inter-agent coordination overhead needed for this use case.

**Q: Why does the agent only call one tool per turn instead of batching?**
The default model (`moonshotai/kimi-k2.6`) hard-rejects more than one `tool_call` per response
(400 `BadRequestError`). `parallel_tool_calls=False` forces one tool call per turn.
`MAX_TOOL_ITERATIONS=8` (not a more obvious 6) exists because a broad question now costs one
iteration *per signal* instead of batching — 5 tools + 1 synthesis turn already uses 6, so 8
leaves margin.

**Q: Why do tools take zero parameters?**
The app monitors one configured repo/project/service via env vars, not an arbitrary target the
model picks. An earlier version let the model pass a target per call; a smaller model would fill
it with a plausible-looking hallucinated value instead of leaving it empty, silently returning
wrong data with no error.

**Q: Why GitHub/Jira through remote MCP instead of calling their REST APIs directly?**
Uses each vendor's official remote MCP server (`api.githubcopilot.com/mcp/`,
`mcp.atlassian.com/v1/mcp/preview`) — a standardized tool surface instead of hand-rolling
per-vendor REST auth and response parsing.

**Q: What happens if NVIDIA NIM is slow, down, or rate-limited?**
The client is deliberately defensive: `timeout=20.0`, `max_retries=1`, connection pooling
disabled. The OpenAI SDK's defaults (600s timeout, 2 retries, pooled keep-alive) turned a
rate-limited or stalled call into what looked like an indefinite hang. `chat.py` catches
`RateLimitError`/`APITimeoutError`/`APIError` and returns a clean 503/504/502 instead of a bare
500 or a hang.

**Q: What if the primary model isn't approved/available on a given NVIDIA account?**
`run_agent` automatically falls back to `NVIDIA_FALLBACK_MODEL`
(`meta/llama-3.1-70b-instruct`) mid-run and stays on it for the rest of that run, rather than
retrying the primary every iteration. NIM model access is per-model/per-account, so a fresh
account can fail on the primary specifically, not NIM as a whole.

**Q: How is multi-turn context/history handled?**
Postgres via async SQLAlchemy; `conversation_id` from the first response threads into
subsequent requests to keep server-side history, converted to OpenAI-style messages each call.

**Q: Why pgvector instead of a dedicated vector database?**
Reuses the same Postgres instance already used for app data — no extra infrastructure.
`CREATE EXTENSION IF NOT EXISTS vector` runs on startup before table creation.

**Q: How does log search (the RAG tool) work?**
30 hand-authored mock CI/CD + CloudWatch-style log entries, embedded via
`nvidia/nv-embedqa-e5-v5` (1024-dim). It's an *asymmetric* embedding model — ingestion embeds
with `input_type="passage"`, search embeds the query with `input_type="query"`; getting that
backwards doesn't error, it just quietly returns worse matches. Indexing runs once at startup
and is idempotent (checks row count first).

**Q: Why that embedding model specifically?**
An earlier, catalog-listed candidate (`baai/bge-m3`) passes `client.models.list()` but 500s on
every real embeddings call on this account — same class of gotcha as the chat model's
per-account approval gate, just discovered live instead of assumed.

## Security / guardrails

**Q: How do you prevent prompt injection via tool output (e.g. a malicious commit message or
issue title)?**
The system prompt explicitly instructs the model to treat tool output as data, never as
instructions, and to decline off-topic or instruction-override ("ignore your previous
instructions...") requests. This was verified live against a jailbreak-style prompt, not just
assumed to work.

**Q: What guardrails exist on the chat endpoint itself?**
422 on empty/whitespace-only or >4000-char messages before the agent is even called; a per-IP
rate limit (default 20/min) returning 429 + `Retry-After`. It's an in-memory sliding window,
single-process only — meant to stop one client from burning API quota, not a security boundary.

**Q: How does auth work?**
JWT access tokens plus an httponly refresh-token cookie. Refresh-token reuse (a token used after
it's already been rotated) is treated as possible theft and revokes every active session for
that user, not just the one token.

**Q: Can this be demoed with zero external credentials?**
Yes — `USE_MOCK_DATA=true` is the default, and every integration client falls back to realistic
mock data when it isn't configured. Monitoring/incidents are *always* mock (no universal vendor
API exists for that). Log search is always the mock corpus by design, not a toggle.

## Extensibility

**Q: How do you add a new signal source?**
Two steps: add a client in `app/integrations/` with an async `fetch_summary()`, then register a
tool schema + one dispatch entry in `app/agents/tools.py`. No changes to the orchestrator loop,
API routes, or frontend.

**Q: What's explicitly not production-ready yet?**
The in-memory rate limiter (needs a shared store for multiple workers); monitoring/incidents
being mock-only (no real provider wired in); no multi-tenant scoping beyond a single user/role
model; no migration tooling (`Base.metadata.create_all`, no Alembic).

## Windows / dev environment

**Q: Any interesting platform-specific issues?**
On Windows, the default `ProactorEventLoop` hangs on some async TLS reads via httpx/anyio (used
by the `openai` client). `app/main.py` forces `WindowsSelectorEventLoopPolicy` to work around it.

## Demo mechanics

**Q: What if the live demo breaks on stage?**
Slide 4 in the deck is an actual screenshot (not a mockup) of a real question answered by the
running app, as a visual fallback. Slide 8 narrates the traced "why did the checkout deploy
fail?" example step-by-step even without the live app up.

**Q: What's a good question to ask live?**
- "Why did the checkout deploy fail?" — routes cleanly through `search_error_logs` → embedding →
  pgvector match → a reply citing the specific log line. Good for showing the RAG path.
- "What's the overall delivery health of the project right now?" — the question used to capture
  slide 4's screenshot; touches 3-4 tools and shows cross-source correlation clearly.
