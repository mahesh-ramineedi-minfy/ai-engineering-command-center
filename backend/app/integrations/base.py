"""
Shared conventions for integration clients.

Each client exposes a single async `fetch_summary(**kwargs) -> dict` method.
If real credentials are configured (see app.core.config.Settings) the client
calls the live API; otherwise it returns realistic mock data so the agent
and UI are fully demoable with zero configuration. Swap in more sources by
following this same shape and registering a tool in app/agents/tools.py.
"""

from typing import Protocol


class IntegrationClient(Protocol):
    async def fetch_summary(self, **kwargs) -> dict: ...
