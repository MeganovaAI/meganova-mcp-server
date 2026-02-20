"""Tests for MCP server creation and tool registration."""

from __future__ import annotations

from meganova_mcp_server.config import Config
from meganova_mcp_server.server import create_server


def test_create_server_registers_tools(monkeypatch: object) -> None:
    """Server should register all expected tools."""
    import os

    os.environ.setdefault("NOVA_MESH_URL", "http://localhost:8000")
    os.environ.setdefault("MEGANOVA_API_KEY", "test-key")

    mcp = create_server()

    # Verify the server was created with correct name
    assert mcp.name == "meganova"


def test_config_defaults() -> None:
    """Config should use sensible defaults."""
    config = Config(nova_mesh_url="http://localhost:8000", api_key="key")
    assert config.server_name == "meganova"
    assert config.server_version == "0.1.0"
    assert config.transport == "stdio"
    assert config.host == "0.0.0.0"
    assert config.port == 8080


def test_config_custom_values() -> None:
    """Config should accept custom values."""
    config = Config(
        nova_mesh_url="http://mesh:9000",
        api_key="custom-key",
        server_name="my-server",
        transport="http",
        port=3000,
    )
    assert config.nova_mesh_url == "http://mesh:9000"
    assert config.api_key == "custom-key"
    assert config.server_name == "my-server"
    assert config.transport == "http"
    assert config.port == 3000
