"""Observability tools — call logs, traces, metrics, graphs, health."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register observability tools on the MCP server."""

    def _headers() -> dict:
        return {"Authorization": f"Bearer {config.api_key}"}

    @mcp.tool()
    async def mesh_call_log(limit: int = 10, agent_id: str = "") -> str:
        """Get recent LLM call records from the mesh.

        Args:
            limit: Number of recent calls to return
            agent_id: Optional filter by agent ID
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            if agent_id:
                resp = await client.get(
                    f"/api/call-log/agents/{agent_id}",
                    params={"limit": limit},
                    headers=_headers(),
                )
            else:
                resp = await client.get(
                    "/api/call-log",
                    params={"limit": limit},
                    headers=_headers(),
                )
            resp.raise_for_status()
            calls = resp.json()

        lines = []
        for call in calls:
            agent = call.get("agent_id", "?")
            model = call.get("model", "?")
            status = call.get("status", "?")
            prompt_tokens = call.get("prompt_tokens", 0)
            completion_tokens = call.get("completion_tokens", 0)
            duration = call.get("duration_ms", "?")
            lines.append(
                f"- [{agent}] {model}: {prompt_tokens}+{completion_tokens} tokens, "
                f"{duration}ms ({status})"
            )
        return "\n".join(lines) if lines else "No recent calls."

    @mcp.tool()
    async def mesh_call_summary(agent_id: str) -> str:
        """Get call summary stats for an agent (total calls, tokens, errors).

        Args:
            agent_id: The agent's ID
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                f"/api/call-log/agents/{agent_id}/summary", headers=_headers()
            )
            resp.raise_for_status()
            data = resp.json()

        import json
        return json.dumps(data, indent=2)

    @mcp.tool()
    async def mesh_traces(limit: int = 10) -> str:
        """Get completed trace spans for debugging.

        Args:
            limit: Number of recent traces to return
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                "/api/traces/completed",
                params={"limit": limit},
                headers=_headers(),
            )
            resp.raise_for_status()
            spans = resp.json()

        lines = []
        for span in spans:
            name = span.get("name", "?")
            trace_id = span.get("trace_id", "?")[:8]
            status = span.get("status", "?")
            duration = ""
            if span.get("start_time") and span.get("end_time"):
                duration = f" ({span['end_time'] - span['start_time']:.0f}ms)" if isinstance(span.get("end_time"), (int, float)) else ""
            lines.append(f"- [{trace_id}] {name}: {status}{duration}")
        return "\n".join(lines) if lines else "No completed traces."

    @mcp.tool()
    async def mesh_metrics() -> str:
        """Get current mesh metrics snapshot (counters, histograms)."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/metrics", headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        import json
        return json.dumps(data, indent=2)

    @mcp.tool()
    async def mesh_cost_summary() -> str:
        """Get token usage cost summary by agent."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/metrics/cost-summary", headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        import json
        return json.dumps(data, indent=2)

    @mcp.tool()
    async def mesh_graph() -> str:
        """Get the full pipeline graph showing agents, stages, and connections."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/graph", headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        parts = [
            f"Graph: {data.get('node_count', len(nodes))} nodes, {data.get('edge_count', len(edges))} edges\n",
            "Nodes:",
        ]
        for node in nodes:
            parts.append(f"  - {node.get('id', '?')} ({node.get('type', '?')})")
        parts.append("\nEdges:")
        for edge in edges:
            parts.append(f"  - {edge.get('source', '?')} → {edge.get('target', '?')}")
        return "\n".join(parts)

    @mcp.tool()
    async def mesh_request_journey(event_id: str) -> str:
        """Get the full journey of a request through the pipeline.

        Args:
            event_id: The event ID from a route/execute response
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(f"/api/graph/journey/{event_id}", headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        event = data.get("event", {})
        spans = data.get("spans", [])
        calls = data.get("call_records", [])

        parts = [
            f"Event: {event.get('event_id', '?')}",
            f"Agent: {event.get('agent_id', '?')}",
            f"Method: {event.get('method', '?')} (confidence: {event.get('confidence', '?')})",
            f"Duration: {event.get('total_duration_ms', '?')}ms",
        ]

        if event.get("brain_ran"):
            parts.append(f"Brain reasoning: {event.get('brain_reasoning', '')}")

        if spans:
            parts.append(f"\nSpans ({len(spans)}):")
            for s in spans:
                parts.append(f"  - {s.get('name', '?')}: {s.get('status', '?')}")

        if calls:
            parts.append(f"\nLLM Calls ({len(calls)}):")
            for c in calls:
                parts.append(
                    f"  - Turn {c.get('turn', '?')}: "
                    f"{c.get('prompt_tokens', 0)}+{c.get('completion_tokens', 0)} tokens"
                )

        return "\n".join(parts)

    @mcp.tool()
    async def mesh_health() -> str:
        """Check Nova Mesh health status including agent and circuit breaker states."""
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/health", headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        import json
        return json.dumps(data, indent=2)

    @mcp.tool()
    async def mesh_eval_run(
        agent_id: str,
        prompt: str = "",
        dataset_json: str = "",
        grader_types: str = "exact",
        k: int = 1,
    ) -> str:
        """Run an evaluation dataset against an agent.

        Args:
            agent_id: Agent to evaluate
            prompt: Single prompt to evaluate (alternative to dataset)
            dataset_json: JSON array of test cases [{"input": ..., "expected": ...}]
            grader_types: Comma-separated grader types (e.g. "exact,semantic")
            k: Number of runs per case
        """
        payload: dict = {"grader_types": [g.strip() for g in grader_types.split(",")], "k": k}
        if agent_id:
            payload["agent_id"] = agent_id
        if prompt:
            payload["prompt"] = prompt
        if dataset_json:
            import json
            payload["dataset_json"] = json.loads(dataset_json)

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/eval/run", json=payload, headers=_headers(), timeout=300
            )
            resp.raise_for_status()
            data = resp.json()

        import json
        return json.dumps(data, indent=2)

    @mcp.tool()
    async def mesh_eval_history(agent_id: str = "", limit: int = 10) -> str:
        """Get historical evaluation run results.

        Args:
            agent_id: Optional filter by agent
            limit: Max results to return
        """
        params: dict = {"limit": limit}
        if agent_id:
            params["agent_id"] = agent_id

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get("/api/eval/history", params=params, headers=_headers())
            resp.raise_for_status()
            data = resp.json()

        import json
        return json.dumps(data, indent=2)
