"""Cloud agent tools — chat with deployed MegaNova Studio agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register cloud agent tools on the MCP server."""

    @mcp.tool()
    async def cloud_agent_info(agent_api_key: str) -> str:
        """Get info about a deployed MegaNova Cloud agent.

        Args:
            agent_api_key: The agent's API key (starts with "agent_")
        """
        async with httpx.AsyncClient(base_url=config.studio_api_url) as client:
            resp = await client.get(
                f"/agents/v1/{agent_api_key}/info",
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        parts = [
            f"Name: {data.get('name', '?')}",
            f"Description: {data.get('description', 'N/A')}",
            f"Available: {data.get('is_available', '?')}",
            f"Welcome: {data.get('welcome_message', '')}",
        ]
        return "\n".join(parts)

    @mcp.tool()
    async def cloud_agent_chat(
        agent_api_key: str,
        message: str,
        conversation_id: str = "",
        user_identifier: str = "",
    ) -> str:
        """Chat with a deployed MegaNova Cloud agent.

        Args:
            agent_api_key: The agent's API key (starts with "agent_")
            message: Message to send to the agent
            conversation_id: Optional conversation ID for multi-turn chat (returned in previous responses)
            user_identifier: Optional user identifier for memory/personalization
        """
        body: dict = {"message": message}
        if conversation_id:
            body["conversation_id"] = conversation_id
        if user_identifier:
            body["user_identifier"] = user_identifier

        async with httpx.AsyncClient(base_url=config.studio_api_url) as client:
            resp = await client.post(
                f"/agents/v1/{agent_api_key}/chat",
                json=body,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        response = data.get("response", "")
        conv_id = data.get("conversation_id", "")
        tokens = data.get("tokens_used", "?")
        memories = data.get("memories_used", 0)

        parts = [response]
        meta = [f"conversation_id: {conv_id}", f"tokens: {tokens}"]
        if memories:
            meta.append(f"memories_used: {memories}")

        pending = data.get("pending_tool_call")
        if pending:
            parts.append(
                f"\n⚠ Pending tool approval: {pending.get('tool_name', '?')}\n"
                f"  Description: {pending.get('description', '')}\n"
                f"  approval_id: {pending.get('approval_id', '')}"
            )

        parts.append(f"\n[{' | '.join(meta)}]")
        return "\n".join(parts)

    @mcp.tool()
    async def cloud_agent_confirm_tool(
        agent_api_key: str,
        approval_id: str,
        action: str = "approve",
    ) -> str:
        """Approve or reject a pending tool call from a Cloud agent.

        Args:
            agent_api_key: The agent's API key (starts with "agent_")
            approval_id: The approval_id from a pending tool call
            action: "approve" or "reject"
        """
        body = {"approval_id": approval_id, "action": action}

        async with httpx.AsyncClient(base_url=config.studio_api_url) as client:
            resp = await client.post(
                f"/agents/v1/{agent_api_key}/chat/confirm",
                json=body,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        response = data.get("response", str(data))
        return f"Tool {action}d.\n\n{response}"
