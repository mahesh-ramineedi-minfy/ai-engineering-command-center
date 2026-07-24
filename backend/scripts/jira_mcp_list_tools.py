"""
Debug helper: connect to Atlassian's remote MCP server with the credentials in
.env and print every available tool's name + input schema (optionally filtered
to one tool by name).

Atlassian's MCP tool names/schemas can't be verified without a live Jira site
(unlike GitHub's remote MCP server, which is usable anonymously against public
docs) — use this to check ground truth before trusting jira_client.py /
jira_mcp.py against a real account, the same way `actions_list`'s schema was
checked for the GitHub CI/CD integration.

Usage:
    python scripts/jira_mcp_list_tools.py
    python scripts/jira_mcp_list_tools.py createJiraIssue
"""

import asyncio
import base64
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.config import settings  # noqa: E402
from app.integrations.jira_mcp import JIRA_MCP_URL  # noqa: E402


async def main() -> None:
    name_filter = sys.argv[1] if len(sys.argv) > 1 else None
    basic = base64.b64encode(f"{settings.jira_email}:{settings.jira_api_token}".encode()).decode()
    headers = {"Authorization": f"Basic {basic}"}

    async with streamablehttp_client(JIRA_MCP_URL, headers=headers, timeout=15) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                if name_filter and tool.name != name_filter:
                    continue
                print(f"\n=== {tool.name} ===")
                print(tool.description)
                print(json.dumps(tool.inputSchema, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
