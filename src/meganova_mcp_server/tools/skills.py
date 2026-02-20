"""Skill tools — execute skills, list available skill packs, search catalog."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register skill tools on the MCP server."""

    @mcp.tool()
    async def list_skills() -> str:
        """List all available skill packs in the Nova Mesh catalog."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                "/api/skills", headers={"Authorization": f"Bearer {config.api_key}"}
            )
            resp.raise_for_status()
            skills = resp.json()

        lines = []
        for skill in skills:
            tool_count = len(skill.get("tools", []))
            lines.append(f"- {skill['name']}: {skill.get('description', '')} ({tool_count} tools)")
        return "\n".join(lines) if lines else "No skills available."

    @mcp.tool()
    async def execute_skill(skill_name: str, tool_name: str, arguments: str = "{}") -> str:
        """Execute a specific tool from a skill pack.

        Args:
            skill_name: Name of the skill pack (e.g., "web", "pdf", "code")
            tool_name: Name of the tool within the skill pack
            arguments: JSON string of arguments to pass to the tool
        """
        import json

        args = json.loads(arguments) if arguments else {}

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                f"/api/skills/{skill_name}/execute",
                json={"tool": tool_name, "arguments": args},
                headers={"Authorization": f"Bearer {config.api_key}"},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("result", str(data))

    @mcp.tool()
    async def search_catalog(query: str) -> str:
        """Search the Nova Mesh skill catalog for tools matching a query.

        Args:
            query: Search query (e.g., "pdf extraction", "web scraping")
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                "/api/catalog/search",
                params={"q": query},
                headers={"Authorization": f"Bearer {config.api_key}"},
            )
            resp.raise_for_status()
            results = resp.json()

        lines = []
        for r in results:
            lines.append(f"- {r['skill']}/{r['tool']}: {r.get('description', '')}")
        return "\n".join(lines) if lines else f"No tools found matching '{query}'."
