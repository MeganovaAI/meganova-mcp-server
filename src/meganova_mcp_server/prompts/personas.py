"""Persona prompts — character system prompts as MCP prompt templates."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register persona prompts on the MCP server."""

    @mcp.prompt()
    def route_task_prompt(task: str, context: str = "") -> str:
        """Generate a prompt for routing a task through Nova Mesh.

        Args:
            task: Description of the task to accomplish
            context: Optional additional context for routing decisions
        """
        parts = [
            "You have access to a Nova Mesh agent network. Route the following task "
            "to the best available agent.\n",
            f"Task: {task}",
        ]
        if context:
            parts.append(f"Context: {context}")
        parts.append(
            "\nUse the route_task tool to send this to the mesh, "
            "or use list_agents to see available agents first."
        )
        return "\n".join(parts)

    @mcp.prompt()
    def agent_chat_prompt(agent_name: str, goal: str) -> str:
        """Generate a prompt for an interactive session with a specific agent.

        Args:
            agent_name: Name of the agent to chat with
            goal: What the user wants to accomplish with this agent
        """
        return (
            f"Start a conversation with the Nova Mesh agent '{agent_name}' "
            f"to accomplish the following goal:\n\n{goal}\n\n"
            f"Use the chat_with_agent tool with agent_name='{agent_name}'. "
            "Use the same session_id across messages to maintain conversation context."
        )

    @mcp.prompt()
    def skill_discovery_prompt(need: str) -> str:
        """Generate a prompt for discovering relevant skills in the catalog.

        Args:
            need: Description of what capability is needed
        """
        return (
            f"Find Nova Mesh skills that can help with: {need}\n\n"
            "Steps:\n"
            "1. Use search_catalog to find matching tools\n"
            "2. Use list_skills to see all available skill packs\n"
            "3. Use execute_skill to run the best matching tool"
        )
