"""Agent resources — expose agent profiles as MCP resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register agent resources on the MCP server."""

    @mcp.resource("nova://agents")
    async def agents_index() -> str:
        """List all registered Nova Mesh agents with roles and capabilities."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                "/api/agents", headers={"Authorization": f"Bearer {config.api_key}"}
            )
            resp.raise_for_status()
            agents = resp.json()

        lines = []
        for agent in agents:
            caps = ", ".join(agent.get("capabilities", []))
            skills = ", ".join(s["name"] for s in agent.get("skills", []))
            lines.append(
                f"## {agent['name']}\n"
                f"- Role: {agent.get('role', 'agent')}\n"
                f"- Model: {agent.get('model', 'unknown')}\n"
                f"- Capabilities: {caps}\n"
                f"- Skills: {skills}"
            )
        return "\n\n".join(lines) if lines else "No agents registered."

    @mcp.resource("nova://agents/{agent_name}")
    async def agent_profile(agent_name: str) -> str:
        """Get detailed profile for a specific Nova Mesh agent."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                f"/api/agents/{agent_name}",
                headers={"Authorization": f"Bearer {config.api_key}"},
            )
            resp.raise_for_status()
            agent = resp.json()

        parts = [
            f"# {agent['name']}",
            f"**Role:** {agent.get('role', 'agent')}",
            f"**Model:** {agent.get('model', 'unknown')}",
        ]
        if agent.get("description"):
            parts.append(f"\n{agent['description']}")
        if agent.get("system_prompt"):
            parts.append(f"\n## System Prompt\n{agent['system_prompt']}")
        if agent.get("capabilities"):
            parts.append(f"\n## Capabilities\n- " + "\n- ".join(agent["capabilities"]))
        if agent.get("skills"):
            parts.append("\n## Skills")
            for skill in agent["skills"]:
                tool_count = len(skill.get("tools", []))
                parts.append(f"- **{skill['name']}**: {skill.get('description', '')} ({tool_count} tools)")
        return "\n".join(parts)
