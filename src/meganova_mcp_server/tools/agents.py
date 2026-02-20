"""Agent tools — list, chat, and inspect Nova Mesh agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register agent tools on the MCP server."""

    @mcp.tool()
    async def list_agents() -> str:
        """List all available Nova Mesh agents with their capabilities and loaded skills."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                "/api/agents", headers={"Authorization": f"Bearer {config.api_key}"}
            )
            resp.raise_for_status()
            agents = resp.json()

        lines = []
        for agent in agents:
            caps = ", ".join(agent.get("capabilities", []))
            lines.append(f"- {agent['name']} ({agent.get('role', 'agent')}): {caps}")
        return "\n".join(lines) if lines else "No agents registered."

    @mcp.tool()
    async def chat_with_agent(agent_name: str, message: str, session_id: str = "") -> str:
        """Send a message to a specific Nova Mesh agent and get a response.

        Args:
            agent_name: Name of the agent to chat with
            message: The message to send
            session_id: Optional session ID for conversation continuity
        """
        payload: dict = {"agent": agent_name, "message": message}
        if session_id:
            payload["session_id"] = session_id

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/chat",
                json=payload,
                headers={"Authorization": f"Bearer {config.api_key}"},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("response", data.get("content", str(data)))

    @mcp.tool()
    async def get_agent_info(agent_name: str) -> str:
        """Get detailed information about a specific agent including its skills and configuration.

        Args:
            agent_name: Name of the agent to inspect
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                f"/api/agents/{agent_name}",
                headers={"Authorization": f"Bearer {config.api_key}"},
            )
            resp.raise_for_status()
            agent = resp.json()

        parts = [
            f"Name: {agent['name']}",
            f"Role: {agent.get('role', 'agent')}",
            f"Model: {agent.get('model', 'unknown')}",
            f"Capabilities: {', '.join(agent.get('capabilities', []))}",
            f"Skills: {', '.join(s['name'] for s in agent.get('skills', []))}",
        ]
        if agent.get("description"):
            parts.insert(1, f"Description: {agent['description']}")
        return "\n".join(parts)
