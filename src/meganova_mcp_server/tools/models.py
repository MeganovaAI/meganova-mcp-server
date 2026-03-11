"""Model discovery tools — list and search available models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register model discovery tools on the MCP server."""

    @mcp.tool()
    async def list_models(
        modality: str = "",
        model_family: str = "",
        highlight: str = "",
        use_case: str = "",
        search: str = "",
    ) -> str:
        """List available MegaNova models with optional filtering.

        Args:
            modality: Filter by modality (comma-separated), e.g. "text_generation", "text_to_image", "multimodal", "embeddings", "reranker", "audio"
            model_family: Filter by family (comma-separated), e.g. "Manta", "OpenAI", "Gemini", "Deepseek", "Qwen"
            highlight: Filter by highlight, e.g. "free", "recently_added", "featured"
            use_case: Filter by use case, e.g. "best_role_play", "best_image_generation"
            search: Search across all tag categories
        """
        # Use the serverless filter endpoint for rich filtering
        base_url = config.api_url.replace("/v1", "")
        params: dict = {"include_tag_counts": "false"}
        if modality:
            params["modality"] = modality
        if model_family:
            params["model_family"] = model_family
        if highlight:
            params["highlight"] = highlight
        if use_case:
            params["use_case"] = use_case
        if search:
            params["search"] = search

        async with httpx.AsyncClient(base_url=base_url) as client:
            resp = await client.get(
                "/api/v1/serverless/models/filter",
                params=params,
                headers={"Authorization": f"Bearer {config.api_key}"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        inner = data.get("data", data)
        models = inner.get("models", [])
        count = inner.get("count", len(models))

        lines = [f"Found {count} model(s):\n"]
        for m in models:
            name = m.get("model_name", "?")
            alias = m.get("model_alias", "")
            ctx = m.get("context_length")
            input_price = m.get("input_price")
            output_price = m.get("output_price")
            tags = m.get("tags", {})
            modalities = ", ".join(tags.get("modality", [])) if tags else ""

            line = f"- **{name}**"
            if alias:
                line += f" ({alias})"
            details = []
            if modalities:
                details.append(modalities)
            if ctx:
                details.append(f"{ctx:,} ctx")
            if input_price is not None:
                details.append(f"${input_price}/M in, ${output_price}/M out")
            if details:
                line += f"  [{', '.join(details)}]"
            lines.append(line)

        return "\n".join(lines)
