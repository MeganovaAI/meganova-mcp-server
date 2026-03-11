"""Inference tools — chat completions, embeddings, reranking via MegaNova API."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register inference tools on the MCP server."""

    def _headers() -> dict:
        return {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    @mcp.tool()
    async def chat_completion(
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request to a MegaNova LLM model.

        Args:
            model: Model name (e.g. "meganova-ai/manta-flash-1.0", "Qwen/Qwen3-235B-A22B-Instruct-2507")
            messages: List of message dicts with "role" and "content" keys
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(base_url=config.api_url) as client:
            resp = await client.post(
                "/chat/completions",
                json=payload,
                headers=_headers(),
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            usage = data.get("usage", {})
            return (
                f"{content}\n\n"
                f"[Model: {data.get('model', model)} | "
                f"Tokens: {usage.get('total_tokens', '?')}]"
            )
        return str(data)

    @mcp.tool()
    async def create_embeddings(
        input: str | list[str],
        model: str,
    ) -> str:
        """Generate text embeddings using a MegaNova embedding model.

        Args:
            input: Text string or list of strings to embed
            model: Embedding model name
        """
        payload = {"input": input, "model": model}

        async with httpx.AsyncClient(base_url=config.api_url) as client:
            resp = await client.post(
                "/embeddings",
                json=payload,
                headers=_headers(),
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

        embeddings = data.get("data", [])
        dims = len(embeddings[0]["embedding"]) if embeddings else 0
        usage = data.get("usage", {})
        return (
            f"Generated {len(embeddings)} embedding(s), {dims} dimensions each.\n"
            f"Tokens used: {usage.get('total_tokens', '?')}\n"
            f"First 5 values: {embeddings[0]['embedding'][:5] if embeddings else '[]'}"
        )

    @mcp.tool()
    async def rerank_documents(
        query: str,
        documents: list[str],
        model: str,
        top_n: int = 5,
    ) -> str:
        """Rerank documents by relevance to a query using a MegaNova reranking model.

        Args:
            query: The search query
            documents: List of document strings to rerank
            model: Reranking model name
            top_n: Number of top results to return
        """
        payload = {
            "query": query,
            "documents": documents,
            "model": model,
            "top_n": top_n,
            "return_documents": True,
        }

        async with httpx.AsyncClient(base_url=config.api_url) as client:
            resp = await client.post(
                "/rerank",
                json=payload,
                headers=_headers(),
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        lines = []
        for r in results:
            score = r.get("relevance_score", 0)
            doc = r.get("document", "")
            preview = doc[:100] + "..." if len(doc) > 100 else doc
            lines.append(f"  [{score:.4f}] {preview}")
        return f"Top {len(results)} results:\n" + "\n".join(lines)
