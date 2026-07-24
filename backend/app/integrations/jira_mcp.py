import base64
import json

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent

from app.core.config import settings

JIRA_MCP_URL = "https://mcp.atlassian.com/v1/mcp/preview"

_cloud_id_cache: str | None = None


async def _resolve_cloud_id() -> str:
    """Resolve JIRA_URL's cloudId via Atlassian's public tenant_info endpoint.

    Deliberately not the getAccessibleAtlassianResources MCP tool: it requires
    read:me/read:account scopes that live outside the "Rovo MCP V2" app-scoped
    API token category, so no combination of scopes on that token category can
    ever satisfy it. tenant_info needs no auth at all and this app only ever
    targets one fixed JIRA_URL, so there's nothing to look up per-call anyway.
    """
    global _cloud_id_cache
    if _cloud_id_cache is None:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{settings.jira_url.rstrip('/')}/_edge/tenant_info")
            resp.raise_for_status()
            _cloud_id_cache = resp.json()["cloudId"]
    return _cloud_id_cache


def _parse_result(result, tool_name: str) -> dict | list:
    if result.isError:
        detail = result.content[0].text if result.content and isinstance(result.content[0], TextContent) else "unknown error"
        raise RuntimeError(f"jira mcp tool '{tool_name}' failed: {detail}")

    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(result.content[0].text)


async def call_tool(name: str, arguments: dict) -> dict | list:
    """Call a tool on Atlassian's remote MCP server and return its parsed JSON result.

    Atlassian API tokens aren't bound to a single site, so every tool call needs an
    explicit cloudId — resolved via _resolve_cloud_id() and injected here.
    """
    cloud_id = await _resolve_cloud_id()

    basic = base64.b64encode(f"{settings.jira_email}:{settings.jira_api_token}".encode()).decode()
    headers = {"Authorization": f"Basic {basic}"}

    async with streamablehttp_client(JIRA_MCP_URL, headers=headers, timeout=15) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, {**arguments, "cloudId": cloud_id})

    return _parse_result(result, name)
