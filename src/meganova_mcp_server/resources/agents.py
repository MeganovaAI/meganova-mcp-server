"""Agent resources — expose agent profiles as MCP resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register agent resources on the MCP server."""

    def _headers() -> dict:
        return {"Authorization": f"Bearer {config.api_key}"}

    @mcp.resource("nova://agents")
    async def agents_index() -> str:
        """List all registered Nova Mesh agents with types, capabilities, and status."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/agents", headers=_headers())
            resp.raise_for_status()
            agents = resp.json()

        lines = []
        for agent in agents:
            agent_id = agent.get("agent_id", "?")
            name = agent.get("name", agent_id)
            agent_type = agent.get("agent_type", "skill")
            caps = ", ".join(agent.get("capabilities", []))
            skills = ", ".join(agent.get("loaded_skills", []))
            status = agent.get("status", "?")
            published = agent.get("published", False)

            lines.append(
                f"## {name} (`{agent_id}`)\n"
                f"- Type: {agent_type}\n"
                f"- Status: {status}"
                + (" [published]" if published else "") + "\n"
                f"- Capabilities: {caps or 'none'}\n"
                f"- Skills: {skills or 'none'}"
            )
        return "\n\n".join(lines) if lines else "No agents registered."

    @mcp.resource("nova://agents/{agent_id}")
    async def agent_profile(agent_id: str) -> str:
        """Get detailed profile for a specific Nova Mesh agent."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(f"/api/agents/{agent_id}", headers=_headers())
            resp.raise_for_status()
            agent = resp.json()

        name = agent.get("name", agent_id)
        parts = [
            f"# {name}",
            f"**ID:** {agent.get('agent_id', '?')}",
            f"**Type:** {agent.get('agent_type', 'skill')}",
            f"**Status:** {agent.get('status', '?')}",
            f"**Published:** {agent.get('published', False)}",
            f"**Model:** {agent.get('model', 'unknown')}",
        ]
        if agent.get("description"):
            parts.append(f"\n{agent['description']}")
        if agent.get("capabilities"):
            parts.append("\n## Capabilities\n- " + "\n- ".join(agent["capabilities"]))
        if agent.get("tags"):
            parts.append(f"\n## Tags\n- " + "\n- ".join(agent["tags"]))
        skills = agent.get("loaded_skills", [])
        if skills:
            parts.append(f"\n## Loaded Skills\n- " + "\n- ".join(skills))
        tool_count = agent.get("tool_count", 0)
        parts.append(f"\n**Tool Count:** {tool_count}")

        cb = agent.get("circuit_breaker", {})
        if cb:
            parts.append(
                f"\n## Circuit Breaker\n"
                f"- State: {cb.get('state', '?')}\n"
                f"- Failures: {cb.get('failure_count', 0)}"
            )

        trust = agent.get("trust", {})
        if trust:
            parts.append(f"\n## Trust\n- Score: {trust.get('score', '?')}")

        return "\n".join(parts)
