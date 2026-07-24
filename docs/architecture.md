# Architecture

Two diagrams: the full component picture, and one representative request traced end-to-end. For
the reasoning behind non-obvious decisions (MCP endpoint quirks, the embedding model swap, the
zero-params tool rule, etc.), see `CLAUDE.md` — this doc is the map, `CLAUDE.md` is the field notes.

## Components

```mermaid
flowchart TB
    subgraph FE["Frontend (React / Vite)"]
        ChatWindow["ChatWindow<br/>(send / retry / error state)"]
        StatusBar["StatusBar<br/>(polls integration status)"]
    end

    subgraph BE["Backend (FastAPI)"]
        direction TB
        ChatRoute["POST /api/chat<br/>rate_limit_chat + ChatRequest validation"]
        StatusRoute["GET /api/integrations/status"]
        Orchestrator["run_agent<br/>tool-use loop, max 8 iterations, one tool call per turn<br/>NVIDIA_MODEL to NVIDIA_FALLBACK_MODEL on failure"]
        Dispatch["tools.py dispatch table<br/>6 tools"]

        subgraph Clients["Integration clients"]
            JiraClient["jira_client"]
            GithubClient["github_client"]
            CicdClient["cicd_client"]
            MonClient["monitoring_client /<br/>incident_client<br/>(always mock)"]
            LogClient["log_search_client"]
        end

        subgraph RAG["RAG pipeline (app/rag/)"]
            MockLogs["mock_logs.py<br/>30 static entries"]
            Ingest["ensure_logs_indexed()<br/>runs once at startup"]
            Embeddings["embeddings.py"]
            SearchLogs["search_logs()"]
        end
    end

    subgraph DB["Postgres (pgvector-enabled)"]
        ConvTable["conversations / messages"]
        LogTable["log_chunks<br/>(vector(1024))"]
    end

    subgraph EXT["External services"]
        NIMChat["NVIDIA NIM<br/>/v1/chat/completions"]
        NIMEmbed["NVIDIA NIM<br/>/v1/embeddings<br/>nvidia/nv-embedqa-e5-v5"]
        GithubMCP["GitHub remote MCP<br/>api.githubcopilot.com/mcp/"]
        JiraMCP["Atlassian remote MCP<br/>mcp.atlassian.com/v1/mcp/preview"]
    end

    ChatWindow -->|"fetch"| ChatRoute
    StatusBar -->|"fetch"| StatusRoute
    ChatRoute --> Orchestrator
    Orchestrator <-->|"chat completions"| NIMChat
    Orchestrator --> Dispatch
    Dispatch --> JiraClient & GithubClient & CicdClient & MonClient & LogClient

    JiraClient -->|"jira_mcp.py"| JiraMCP
    GithubClient -->|"github_mcp.py"| GithubMCP
    CicdClient -->|"github_mcp.py<br/>actions_list tool"| GithubMCP
    LogClient --> SearchLogs

    Ingest --> MockLogs
    Ingest --> Embeddings
    SearchLogs --> Embeddings
    Embeddings <-->|"embed()"| NIMEmbed
    Ingest --> LogTable
    SearchLogs -->|"cosine distance"| LogTable

    ChatRoute --> ConvTable
```

## Request lifecycle: "why did the checkout deploy fail?"

Traced end-to-end because it's the newest, least obvious path — it touches guardrails, the tool
loop, an embedding call, and pgvector, all in one request.

```mermaid
sequenceDiagram
    participant U as User (ChatWindow)
    participant API as POST /api/chat
    participant O as run_agent (orchestrator)
    participant NIM as NVIDIA NIM (chat)
    participant T as search_error_logs
    participant EMB as NVIDIA NIM (embeddings)
    participant PG as Postgres (log_chunks)

    U->>API: "why did the checkout deploy fail?"
    API->>API: rate_limit_chat (per-IP) + ChatRequest validation
    API->>O: run_agent(message, history)
    O->>NIM: chat.completions.create(tools=[...6 tools])
    NIM-->>O: tool_call: search_error_logs(query="checkout deploy failure")
    O->>T: run_tool("search_error_logs", {query})
    T->>EMB: embed([query], input_type="query")
    EMB-->>T: 1024-dim vector
    T->>PG: ORDER BY embedding <=> query_vec LIMIT 5
    PG-->>T: top matches (e.g. cw-011: 500 error rate jump, rolled back)
    T-->>O: results (log_id, source, content, relevance)
    O->>NIM: chat.completions.create(...)  # with tool result appended
    NIM-->>O: final reply citing the matched log line
    O-->>API: (reply_text, tool_calls trace)
    API-->>U: 200 { reply, tool_calls }
```

If the primary model (`NVIDIA_MODEL`) fails at either chat-completions call, `run_agent` retries
once against `NVIDIA_FALLBACK_MODEL` and continues the run on it — not shown above to keep the
happy path readable, see `CLAUDE.md`'s fallback-model paragraph.
