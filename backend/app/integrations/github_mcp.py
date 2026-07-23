import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent

from app.core.config import settings

GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"
GITHUB_MCP_TOOLSETS = "repos,pull_requests,actions"


async def call_tool(name: str, arguments: dict) -> dict | list:
    """Call a tool on GitHub's remote MCP server and return its parsed JSON result."""
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "X-MCP-Toolsets": GITHUB_MCP_TOOLSETS,
    }
    async with streamablehttp_client(GITHUB_MCP_URL, headers=headers, timeout=15) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)

    if result.isError:
        detail = result.content[0].text if result.content and isinstance(result.content[0], TextContent) else "unknown error"
        raise RuntimeError(f"github mcp tool '{name}' failed: {detail}")

    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(result.content[0].text)
