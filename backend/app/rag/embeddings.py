from typing import Literal

import httpx
from openai import AsyncOpenAI

from app.core.config import settings

EMBEDDING_DIM = 1024  # nvidia/nv-embedqa-e5-v5's output size — must match LogChunk.embedding

_client = AsyncOpenAI(
    api_key=settings.nvidia_api_key,
    base_url=settings.nvidia_base_url,
    # Same defensive config as app/agents/orchestrator.py's client — same host,
    # same failure modes (slow/stalled calls, stale pooled connections).
    timeout=20.0,
    max_retries=1,
    http_client=httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=0)),
)


async def embed(texts: list[str], input_type: Literal["query", "passage"]) -> list[list[float]]:
    """Embed a batch of texts via NVIDIA NIM's /v1/embeddings endpoint.

    nv-embedqa-e5-v5 is an "asymmetric" retrieval model — it embeds search
    queries and the passages they're matched against differently, so callers
    must say which one this batch is. Ingestion (mock_logs.py entries) uses
    "passage"; search_logs()'s query embedding uses "query".
    """
    response = await _client.embeddings.create(
        model=settings.nvidia_embedding_model,
        input=texts,
        extra_body={"input_type": input_type},
    )
    return [item.embedding for item in response.data]
