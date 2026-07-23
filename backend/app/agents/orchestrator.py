"""
The orchestrator agent: a single tool-use loop against an NVIDIA NIM-hosted
model (OpenAI-compatible chat completions API) that investigates a
manager's question by calling specialized signal-source tools (Jira,
GitHub, CI/CD, monitoring, incidents), correlates the results, and returns
an executive-ready answer.

This is intentionally one orchestrating agent with several tools rather
than N separate agent processes — it's simpler to reason about and easy to
extend for a hackathon. If you want true multi-agent delegation (e.g. a
"risk investigator" sub-agent that itself loops over tools before handing
a summary back), split run_agent's tool-execution step into a call to a
nested agent loop per tool/domain.
"""

import json

import httpx
from openai import AsyncOpenAI

from app.agents.tools import TOOLS, run_tool
from app.core.config import settings

SYSTEM_PROMPT = """You are the orchestrator agent for an engineering operations intelligence \
platform. Engineering leaders ask you about sprint health, release risk, technical debt, \
deployment failures, and team productivity.

You have tools that pull live signals from Jira (sprint progress), GitHub (code activity), \
CI/CD (build/deploy status), monitoring (uptime), and incident history. Use them to investigate \
before answering — but only call the tools relevant to the question asked. A question scoped \
to one system (e.g. "recent code activity") needs one tool call, not all five. Call multiple \
tools only when the question genuinely spans more than one system, or when correlating findings \
requires it (e.g. a spike in failed builds plus an open incident plus a blocked sprint issue is \
a single risk story, not three unrelated facts) — broad questions like "release risk" or \
"delivery health" do warrant pulling several signals.

Answer like a briefing for a busy engineering leader:
- Lead with the direct answer / risk level.
- Cite the specific numbers you found.
- Call out correlations across systems explicitly.
- End with concrete recommended actions (backlog reprioritization, resourcing, escalation) when relevant.
Keep it tight — no filler, no restating the question.
"""

MAX_TOOL_ITERATIONS = 6

_client = AsyncOpenAI(
    api_key=settings.nvidia_api_key,
    base_url=settings.nvidia_base_url,
    # Default SDK timeout is 600s and default max_retries is 2 — against a
    # rate-limited key that's up to several minutes of silent backoff before
    # an error ever surfaces to the caller. Fail fast instead: one retry,
    # short per-attempt timeout.
    timeout=20.0,
    max_retries=1,
    # Pooled keep-alive connections to this host intermittently go silent
    # mid-request on this network (plain curl, which never reuses a
    # connection, is consistently fast) — disable reuse so every call opens
    # a fresh connection instead of risking a stale one.
    http_client=httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=0)),
)


async def run_agent(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    """Run the tool-use loop. Returns (final_text, tool_call_trace)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history, {"role": "user", "content": user_message}]
    trace: list[dict] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = await _client.chat.completions.create(
            model=settings.nvidia_model,
            max_tokens=1500,
            tools=TOOLS,
            messages=messages,
        )
        choice = response.choices[0].message

        if not choice.tool_calls:
            return choice.content or "", trace

        messages.append(
            {
                "role": "assistant",
                "content": choice.content,
                "tool_calls": [tc.model_dump() for tc in choice.tool_calls],
            }
        )

        for tool_call in choice.tool_calls:
            tool_input = json.loads(tool_call.function.arguments or "{}")
            result = await run_tool(tool_call.function.name, tool_input)
            trace.append({"tool": tool_call.function.name, "input": tool_input, "summary": _summarize(result)})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

    return "I gathered a lot of signal but couldn't converge on an answer in time — try narrowing the question.", trace


def _summarize(result: dict) -> str:
    keys = [k for k in result.keys() if k not in ("source", "note")]
    parts = [f"{k}={result[k]}" for k in keys[:4]]
    return ", ".join(parts)
