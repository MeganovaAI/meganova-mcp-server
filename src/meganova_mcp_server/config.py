"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """MCP server configuration."""

    # Nova Mesh connection
    nova_mesh_url: str = field(
        default_factory=lambda: os.getenv("NOVA_MESH_URL", "http://localhost:8100")
    )
    api_key: str = field(default_factory=lambda: os.getenv("MEGANOVA_API_KEY", ""))

    # MegaNova API (inference, images, embeddings, etc.)
    api_url: str = field(
        default_factory=lambda: os.getenv("MEGANOVA_API_URL", "https://api.meganova.ai/v1")
    )

    # Studio API (cloud agents)
    studio_api_url: str = field(
        default_factory=lambda: os.getenv("MEGANOVA_STUDIO_URL", "https://studio-api.meganova.ai")
    )

    # Server identity
    server_name: str = field(
        default_factory=lambda: os.getenv("MCP_SERVER_NAME", "meganova")
    )
    server_version: str = "0.2.0"

    # Transport
    transport: str = field(default_factory=lambda: os.getenv("MCP_TRANSPORT", "stdio"))
    host: str = field(default_factory=lambda: os.getenv("MCP_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "8200")))


def load_config() -> Config:
    """Load configuration from environment."""
    return Config()
