from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.models.log_chunk import LogChunk
from app.rag.embeddings import embed
from app.rag.mock_logs import MOCK_LOGS


async def ensure_logs_indexed() -> None:
    """Embed and store the mock log corpus, once. Called from main.py's lifespan.

    Idempotent — checks row count first, so restarts don't re-embed or
    duplicate rows.
    """
    async with async_session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(LogChunk))
        if count:
            return

        vectors = await embed([log["content"] for log in MOCK_LOGS], input_type="passage")
        session.add_all(
            LogChunk(
                log_id=log["id"],
                source=log["source"],
                service=log["service"],
                content=log["content"],
                embedding=vector,
            )
            for log, vector in zip(MOCK_LOGS, vectors, strict=True)
        )
        await session.commit()


async def search_logs(query: str, top_k: int = 5) -> list[dict]:
    """Semantic search over the indexed log corpus. Returns closest matches first."""
    [query_vector] = await embed([query], input_type="query")

    async with async_session_factory() as session:
        distance = LogChunk.embedding.cosine_distance(query_vector)
        result = await session.execute(
            select(LogChunk, distance.label("distance")).order_by(distance).limit(top_k)
        )
        return [
            {
                "log_id": chunk.log_id,
                "source": chunk.source,
                "service": chunk.service,
                "content": chunk.content,
                "relevance": round(1 - dist, 3),
            }
            for chunk, dist in result.all()
        ]
