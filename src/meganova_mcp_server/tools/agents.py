"""Agent tools — list, chat, manage, and inspect Nova Mesh agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register agent tools on the MCP server."""

    def _headers() -> dict:
        return {"Authorization": f"Bearer {config.api_key}"}

    @mcp.tool()
    async def mesh_list_agents() -> str:
        """List all registered Nova Mesh agents with their capabilities, status, and type."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/agents", headers=_headers())
            resp.raise_for_status()
            agents = resp.json()

        lines = []
        for agent in agents:
            caps = ", ".join(agent.get("capabilities", []))
            agent_type = agent.get("agent_type", "skill")
            status = agent.get("status", "?")
            published = agent.get("published", False)
            skills = agent.get("loaded_skills", [])
            skill_names = ", ".join(skills) if skills else "none"
            line = f"- **{agent.get('name', agent.get('agent_id', '?'))}** [{agent_type}] (status: {status})"
            if published:
                line += " [published]"
            line += f"\n  Capabilities: {caps or 'none'}"
            line += f"\n  Skills: {skill_names}"
            lines.append(line)
        return "\n".join(lines) if lines else "No agents registered."

    @mcp.tool()
    async def mesh_get_agent(agent_id: str) -> str:
        """Get detailed information about a specific Nova Mesh agent.

        Args:
            agent_id: The agent's ID
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(f"/api/agents/{agent_id}", headers=_headers())
            resp.raise_for_status()
            agent = resp.json()

        parts = [
            f"Agent ID: {agent.get('agent_id', '?')}",
            f"Name: {agent.get('name', '?')}",
            f"Type: {agent.get('agent_type', 'skill')}",
            f"Status: {agent.get('status', '?')}",
            f"Published: {agent.get('published', False)}",
            f"Model: {agent.get('model', 'unknown')}",
            f"Capabilities: {', '.join(agent.get('capabilities', []))}",
            f"Tags: {', '.join(agent.get('tags', []))}",
        ]
        if agent.get("description"):
            parts.insert(2, f"Description: {agent['description']}")

        skills = agent.get("loaded_skills", [])
        if skills:
            parts.append(f"Loaded Skills: {', '.join(skills)}")

        tool_count = agent.get("tool_count", 0)
        parts.append(f"Tool Count: {tool_count}")

        cb = agent.get("circuit_breaker", {})
        if cb:
            parts.append(f"Circuit Breaker: {cb.get('state', '?')} (failures: {cb.get('failure_count', 0)})")

        trust = agent.get("trust", {})
        if trust:
            parts.append(f"Trust Score: {trust.get('score', '?')}")

        return "\n".join(parts)

    @mcp.tool()
    async def mesh_register_agent(
        agent_id: str,
        name: str,
        description: str = "",
        capabilities: str = "",
        agent_type: str = "skill",
        model: str = "",
        system_prompt: str = "",
    ) -> str:
        """Register a new agent in the Nova Mesh.

        Args:
            agent_id: Unique identifier for the agent
            name: Display name
            description: Agent description
            capabilities: Comma-separated capabilities (e.g. "research,analysis,coding")
            agent_type: "skill" or "persona"
            model: LLM model to use (e.g. "meganova-ai/manta-flash-1.0")
            system_prompt: System prompt for the agent
        """
        payload: dict = {
            "agent_id": agent_id,
            "name": name,
            "agent_type": agent_type,
        }
        if description:
            payload["description"] = description
        if capabilities:
            payload["capabilities"] = [c.strip() for c in capabilities.split(",")]
        if model:
            payload["model"] = model
        if system_prompt:
            payload["system_prompt"] = system_prompt

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post("/api/agents/register", json=payload, headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        return f"Agent '{name}' registered as {agent_id}."

    @mcp.tool()
    async def mesh_update_agent(
        agent_id: str,
        name: str = "",
        description: str = "",
        capabilities: str = "",
        tags: str = "",
        published: bool | None = None,
    ) -> str:
        """Update an existing Nova Mesh agent's profile.

        Args:
            agent_id: The agent's ID
            name: New display name (empty to keep current)
            description: New description (empty to keep current)
            capabilities: Comma-separated capabilities (empty to keep current)
            tags: Comma-separated tags (empty to keep current)
            published: Set published status (None to keep current)
        """
        payload: dict = {}
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description
        if capabilities:
            payload["capabilities"] = [c.strip() for c in capabilities.split(",")]
        if tags:
            payload["tags"] = [t.strip() for t in tags.split(",")]
        if published is not None:
            payload["published"] = published

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.patch(
                f"/api/agents/{agent_id}", json=payload, headers=_headers()
            )
            resp.raise_for_status()

        return f"Agent '{agent_id}' updated."

    @mcp.tool()
    async def mesh_delete_agent(agent_id: str) -> str:
        """Delete/unregister an agent from the Nova Mesh.

        Args:
            agent_id: The agent's ID to delete
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.delete(f"/api/agents/{agent_id}", headers=_headers())
            resp.raise_for_status()

        return f"Agent '{agent_id}' deleted."

    @mcp.tool()
    async def mesh_agent_tools(agent_id: str) -> str:
        """List all tools available to a Nova Mesh agent.

        Args:
            agent_id: The agent's ID
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(f"/api/agents/{agent_id}/tools", headers=_headers())
            resp.raise_for_status()
            tools = resp.json()

        lines = []
        for tool in tools:
            name = tool.get("name", "?")
            desc = tool.get("description", "")
            lines.append(f"- **{name}**: {desc}")
        return "\n".join(lines) if lines else "No tools loaded."

    @mcp.tool()
    async def mesh_agent_memory(agent_id: str) -> str:
        """Inspect an agent's current memory state.

        Args:
            agent_id: The agent's ID
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(f"/api/agents/{agent_id}/memory", headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        return str(data)

    @mcp.tool()
    async def mesh_clear_agent_memory(agent_id: str) -> str:
        """Clear an agent's memory state.

        Args:
            agent_id: The agent's ID
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.delete(f"/api/agents/{agent_id}/memory", headers=_headers())
            resp.raise_for_status()

        return f"Memory cleared for agent '{agent_id}'."

    @mcp.tool()
    async def mesh_agent_think_log(agent_id: str) -> str:
        """Get the think-tool reasoning traces for an agent.

        Args:
            agent_id: The agent's ID
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(f"/api/agents/{agent_id}/think-log", headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        if not data:
            return "No think-log entries."

        lines = []
        for entry in data:
            lines.append(f"- {entry}")
        return "\n".join(lines)

    @mcp.tool()
    async def mesh_delegate_task(agent_id: str, delegate_to: str, task: str) -> str:
        """Delegate a task from one agent to another in the mesh.

        Args:
            agent_id: The delegating agent's ID
            delegate_to: The target agent's ID
            task: Task description to delegate
        """
        payload = {"delegate_to": delegate_to, "task": task}

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                f"/api/agents/{agent_id}/delegate",
                json=payload,
                headers=_headers(),
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("result", str(data))

    @mcp.tool()
    async def mesh_agent_sessions(agent_id: str, limit: int = 10) -> str:
        """List saved conversation sessions for an agent.

        Args:
            agent_id: The agent's ID
            limit: Max sessions to return
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                f"/api/agents/{agent_id}/sessions",
                params={"limit": limit},
                headers=_headers(),
            )
            resp.raise_for_status()
            sessions = resp.json()

        if not sessions:
            return "No saved sessions."

        lines = []
        for s in sessions:
            sid = s.get("session_id", "?")
            meta = s.get("metadata", {})
            lines.append(f"- {sid}: {meta}")
        return "\n".join(lines)

    @mcp.tool()
    async def mesh_save_session(agent_id: str, session_id: str = "") -> str:
        """Save the current agent memory as a named session.

        Args:
            agent_id: The agent's ID
            session_id: Optional session name (auto-generated if empty)
        """
        payload: dict = {}
        if session_id:
            payload["session_id"] = session_id

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                f"/api/agents/{agent_id}/sessions",
                json=payload,
                headers=_headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        return f"Session saved: {data.get('session_id', '?')}"

    @mcp.tool()
    async def mesh_restore_session(agent_id: str, session_id: str) -> str:
        """Restore a saved session to an agent's memory.

        Args:
            agent_id: The agent's ID
            session_id: The session ID to restore
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                f"/api/agents/{agent_id}/sessions/{session_id}/restore",
                headers=_headers(),
            )
            resp.raise_for_status()

        return f"Session '{session_id}' restored for agent '{agent_id}'."

    @mcp.tool()
    async def mesh_reload_skill(agent_id: str, skill_name: str) -> str:
        """Hot-reload a skill on an agent.

        Args:
            agent_id: The agent's ID
            skill_name: Name of the skill to reload
        """
        payload = {"skill_name": skill_name}

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                f"/api/agents/{agent_id}/skills/reload",
                json=payload,
                headers=_headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        return f"Skill '{skill_name}' reloaded on agent '{agent_id}'."

    @mcp.tool()
    async def mesh_agent_checkpoint(agent_id: str) -> str:
        """Export an agent's full checkpoint (config + memory + state).

        Args:
            agent_id: The agent's ID
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                f"/api/agents/{agent_id}/checkpoint", headers=_headers()
            )
            resp.raise_for_status()
            data = resp.json()

        import json
        return json.dumps(data, indent=2)
