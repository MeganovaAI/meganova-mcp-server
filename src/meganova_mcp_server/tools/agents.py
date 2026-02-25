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
                "/api/agents", headers=config.auth_headers()
            )
            resp.raise_for_status()
            data = resp.json()
            agents = data.get("agents", data) if isinstance(data, dict) else data

        lines = []
        for agent in agents:
            agent_id = agent.get("agent_id", "?")
            caps = ", ".join(agent.get("capabilities", []))
            lines.append(f"- [{agent_id}] {agent['name']} ({agent.get('agent_type', 'agent')}): {caps}")
        return "\n".join(lines) if lines else "No agents registered."

    @mcp.tool()
    async def chat_with_agent(agent_name: str, message: str, session_id: str = "") -> str:
        """Send a message to a specific Nova Mesh agent and get a response.

        Uses route/execute to send a prompt to the mesh. If agent_name is provided,
        it will be included as context for routing.

        Args:
            agent_name: Name of the agent to chat with (agent_id from list_agents)
            message: The message to send
            session_id: Optional session ID for conversation continuity
        """
        prompt = f"[target agent: {agent_name}] {message}" if agent_name else message

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/route/execute",
                json={"prompt": prompt},
                headers=config.auth_headers(),
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        agent_id = data.get("agent_id", "unknown")
        output = data.get("output", str(data))
        tokens = data.get("tokens_used", 0)
        return f"[{agent_id}] ({tokens} tokens)\n{output}"

    @mcp.tool()
    async def get_agent_info(agent_name: str) -> str:
        """Get detailed information about a specific agent including its skills and configuration.

        Args:
            agent_name: Name of the agent to inspect (use agent_id from list_agents, e.g. "skill_pdf")
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                f"/api/agents/{agent_name}",
                headers=config.auth_headers(),
            )
            resp.raise_for_status()
            agent = resp.json()

        parts = [
            f"Name: {agent['name']}",
            f"Agent ID: {agent.get('agent_id', 'unknown')}",
            f"Type: {agent.get('agent_type', 'agent')}",
            f"Status: {agent.get('status', 'unknown')}",
            f"Capabilities: {', '.join(agent.get('capabilities', []))}",
            f"Loaded Skills: {', '.join(agent.get('loaded_skills', []))}",
        ]
        if agent.get("description"):
            parts.insert(1, f"Description: {agent['description']}")
        return "\n".join(parts)
