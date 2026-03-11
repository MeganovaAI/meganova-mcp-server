"""Skill tools — list skills, search catalog, list presets."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register skill tools on the MCP server."""

    def _headers() -> dict:
        return {"Authorization": f"Bearer {config.api_key}"}

    @mcp.tool()
    async def mesh_list_skills() -> str:
        """List all available skill packs in the Nova Mesh."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/skills", headers=_headers())
            resp.raise_for_status()
            skills = resp.json()

        lines = []
        for skill in skills:
            tool_count = len(skill.get("tools", []))
            lines.append(
                f"- **{skill['name']}**: {skill.get('description', '')} ({tool_count} tools)"
            )
        return "\n".join(lines) if lines else "No skills available."

    @mcp.tool()
    async def mesh_list_presets() -> str:
        """List available agent presets (pre-configured agent templates)."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/skills/presets", headers=_headers())
            resp.raise_for_status()
            presets = resp.json()

        lines = []
        for preset in presets:
            name = preset.get("name", "?")
            desc = preset.get("description", "")
            lines.append(f"- **{name}**: {desc}")
        return "\n".join(lines) if lines else "No presets available."

    @mcp.tool()
    async def mesh_search_catalog(query: str = "", capability: str = "") -> str:
        """Search the Nova Mesh skill catalog for tools matching a query or capability.

        Args:
            query: Free-text search query (e.g., "pdf extraction", "web scraping")
            capability: Filter by capability name
        """
        params: dict = {}
        if query:
            params["q"] = query
        if capability:
            params["capability"] = capability

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/catalog/search", params=params, headers=_headers())
            resp.raise_for_status()
            results = resp.json()

        lines = []
        for r in results:
            skill = r.get("skill", "?")
            tool = r.get("tool", "?")
            desc = r.get("description", "")
            lines.append(f"- **{skill}/{tool}**: {desc}")
        return "\n".join(lines) if lines else f"No tools found matching '{query or capability}'."

    @mcp.tool()
    async def mesh_sync_catalog() -> str:
        """Sync the skill catalog from all registered sources."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post("/api/catalog/sync", headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        return f"Catalog synced: {data}"
