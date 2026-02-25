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
        prompt = f"{task}\n\nContext: {context}" if context else task

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/route",
                json={"prompt": prompt},
                headers=config.auth_headers(),
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        agent_id = data.get("agent_id", "unknown")
        confidence = data.get("confidence", 0.0)
        method = data.get("method", "unknown")
        cb = data.get("circuit_breaker")

        parts = [
            f"Routed to: {agent_id}",
            f"Confidence: {confidence:.2f}",
            f"Method: {method}",
        ]
        if cb:
            parts.append(f"Circuit Breaker: {cb}")
        return "\n".join(parts)

    @mcp.tool()
    async def execute_dag(plan: str) -> str:
        """Execute a multi-step DAG (directed acyclic graph) plan through the mesh.

        Args:
            plan: JSON string describing the DAG execution plan. Each task needs:
                  task_id, agent_id, prompt, and optional dependencies (list of task_ids).
                  Example: {"tasks": [{"task_id": "t1", "agent_id": "skill_web", "prompt": "search for X"}]}
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

        success = data.get("success", False)
        tasks = data.get("tasks", [])
        order = data.get("execution_order", [])

        lines = [f"Success: {success}", f"Execution order: {order}"]
        for t in tasks:
            status = t.get("status", "?")
            error = t.get("error")
            line = f"- [{t.get('task_id')}] {t.get('name', '?')}: {status}"
            if error:
                line += f" (error: {error})"
            lines.append(line)
        return "\n".join(lines)

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
