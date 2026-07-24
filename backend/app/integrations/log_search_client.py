from app.rag.ingest import search_logs


class LogSearchClient:
    """Semantic search over the mock CI/CD + CloudWatch-style log corpus (see app/rag/)."""

    async def search(self, query: str) -> dict:
        try:
            results = await search_logs(query)
        except Exception:
            results = []

        return {
            "source": "logs",
            "query": query,
            "results": results,
            "note": "mock log corpus (app/rag/mock_logs.py) — not a live CI/CD or CloudWatch feed",
        }


log_search_client = LogSearchClient()
