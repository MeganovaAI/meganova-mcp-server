"""Routing tools — task routing, DAG execution, mesh topology."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register routing tools on the MCP server."""

    @mcp.tool()
    async def route_task(task: str, context: str = "") -> str:
        """Route a task through the Nova Mesh — automatically selects the best agent.

        Args:
            task: Description of the task to accomplish
            context: Optional additional context for routing decisions
        """
        payload: dict = {"task": task}
        if context:
            payload["context"] = context

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/routing/route",
                json=payload,
                headers=config.auth_headers(),
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        parts = [f"Routed to: {data.get('agent', 'unknown')}"]
        if data.get("reasoning"):
            parts.append(f"Reasoning: {data['reasoning']}")
        if data.get("response"):
            parts.append(f"\n{data['response']}")
        return "\n".join(parts)

    @mcp.tool()
    async def execute_dag(plan: str) -> str:
        """Execute a multi-step DAG (directed acyclic graph) plan through the mesh.

        Args:
            plan: JSON string describing the DAG execution plan with steps and dependencies
        """
        import json

        dag = json.loads(plan)

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/execution/dag",
                json=dag,
                headers=config.auth_headers(),
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("result", str(data))

    @mcp.tool()
    async def get_call_log(limit: int = 10) -> str:
        """Get recent LLM call history from the mesh for debugging and observability.

        Args:
            limit: Number of recent calls to return (default: 10)
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                "/api/call-log",
                params={"limit": limit},
                headers=config.auth_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            calls = data.get("records", data) if isinstance(data, dict) else data

        lines = []
        for call in calls:
            model = call.get("model", "?")
            tokens = call.get("total_tokens", 0)
            agent = call.get("agent", "?")
            lines.append(f"- [{agent}] {model}: {tokens} tokens")
        return "\n".join(lines) if lines else "No recent calls."
