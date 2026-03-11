"""Routing tools — task routing, execution, eval-opt, and chat via Nova Mesh."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register routing and execution tools on the MCP server."""

    def _headers() -> dict:
        return {"Authorization": f"Bearer {config.api_key}"}

    @mcp.tool()
    async def mesh_route(prompt: str, candidate_ids: str = "") -> str:
        """Route a prompt to the best agent using 3-tier cascade (rules → semantic → LLM).

        Args:
            prompt: The task or question to route
            candidate_ids: Optional comma-separated agent IDs to limit routing to
        """
        payload: dict = {"prompt": prompt}
        if candidate_ids:
            payload["candidate_ids"] = [c.strip() for c in candidate_ids.split(",")]

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post("/api/route", json=payload, headers=_headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()

        agent_id = data.get("agent_id", "none")
        confidence = data.get("confidence", 0)
        method = data.get("method", "?")
        delegation_id = data.get("delegation_id", "")

        parts = [
            f"Routed to: {agent_id}",
            f"Confidence: {confidence}",
            f"Method: {method}",
        ]
        if delegation_id:
            parts.append(f"Delegation ID: {delegation_id}")

        cb = data.get("circuit_breaker")
        if cb:
            parts.append(f"Circuit Breaker: {cb}")

        return "\n".join(parts)

    @mcp.tool()
    async def mesh_route_and_execute(prompt: str, candidate_ids: str = "") -> str:
        """Route a prompt to the best agent AND execute it in one call.

        Args:
            prompt: The task or question to route and execute
            candidate_ids: Optional comma-separated agent IDs to limit routing to
        """
        payload: dict = {"prompt": prompt}
        if candidate_ids:
            payload["candidate_ids"] = [c.strip() for c in candidate_ids.split(",")]

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/route/execute", json=payload, headers=_headers(), timeout=120
            )
            resp.raise_for_status()
            data = resp.json()

        agent_id = data.get("agent_id", "?")
        output = data.get("output", "")
        tokens = data.get("tokens_used", "?")
        tool_calls = data.get("tool_calls_made", 0)

        parts = [output]
        meta = [f"Agent: {agent_id}", f"Tokens: {tokens}"]
        if tool_calls:
            meta.append(f"Tool calls: {tool_calls}")
        event_id = data.get("event_id")
        if event_id:
            meta.append(f"Event: {event_id}")

        parts.append(f"\n[{' | '.join(meta)}]")
        return "\n".join(parts)

    @mcp.tool()
    async def mesh_chat(api_key: str, message: str, conversation_id: str = "") -> str:
        """Multi-turn chat with a Nova Mesh PersonaAgent via its API key.

        Args:
            api_key: The agent's API key (from reveal-key)
            message: Message to send
            conversation_id: Optional conversation ID for multi-turn continuity
        """
        payload: dict = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                f"/agents/v1/{api_key}/chat",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        response = data.get("response", "")
        conv_id = data.get("conversation_id", "")

        parts = [response]

        images = data.get("images", [])
        if images:
            parts.append(f"\nImages: {len(images)} generated")

        files = data.get("files", [])
        if files:
            parts.append(f"Files: {', '.join(files)}")

        parts.append(f"\n[conversation_id: {conv_id}]")
        return "\n".join(parts)

    @mcp.tool()
    async def mesh_eval_opt(
        generator_id: str,
        evaluator_id: str,
        prompt: str,
        max_iterations: int = 3,
    ) -> str:
        """Run evaluator-optimizer refinement loop between two agents.

        The generator produces output, the evaluator critiques it, and they iterate
        until quality is acceptable or max iterations is reached.

        Args:
            generator_id: Agent ID of the generator
            evaluator_id: Agent ID of the evaluator
            prompt: The initial prompt to refine
            max_iterations: Maximum refinement iterations
        """
        payload = {
            "generator_id": generator_id,
            "evaluator_id": evaluator_id,
            "prompt": prompt,
            "max_iterations": max_iterations,
        }

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/execution/eval-opt",
                json=payload,
                headers=_headers(),
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()

        return str(data)

    @mcp.tool()
    async def mesh_harness(
        initializer_id: str,
        worker_id: str,
        goal: str,
        max_sessions: int = 3,
    ) -> str:
        """Run a two-agent harness: initializer sets up context, worker executes.

        Args:
            initializer_id: Agent ID of the initializer
            worker_id: Agent ID of the worker
            goal: The goal to accomplish
            max_sessions: Maximum work sessions
        """
        payload = {
            "initializer_id": initializer_id,
            "worker_id": worker_id,
            "goal": goal,
            "max_sessions": max_sessions,
        }

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/execution/harness",
                json=payload,
                headers=_headers(),
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()

        return str(data)

    @mcp.tool()
    async def mesh_delegation_status(delegation_id: str) -> str:
        """Check the status of a routing delegation.

        Args:
            delegation_id: The delegation ID from a route response
        """
        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.get(
                f"/api/route/status/{delegation_id}", headers=_headers()
            )
            resp.raise_for_status()
            data = resp.json()

        return str(data)

    @mcp.tool()
    async def mesh_route_feedback(
        delegation_id: str,
        status: str,
        duration_ms: int = 0,
        tokens_used: int = 0,
    ) -> str:
        """Report outcome of a delegation for routing quality improvement.

        Args:
            delegation_id: The delegation ID
            status: Outcome status (e.g. "success", "failure")
            duration_ms: Execution duration in milliseconds
            tokens_used: Tokens consumed
        """
        payload = {
            "delegation_id": delegation_id,
            "status": status,
            "duration_ms": duration_ms,
            "tokens_used": tokens_used,
        }

        async with httpx.AsyncClient(base_url=config.nova_mesh_url) as client:
            resp = await client.post(
                "/api/route/feedback", json=payload, headers=_headers()
            )
            resp.raise_for_status()

        return f"Feedback recorded for delegation '{delegation_id}'."
