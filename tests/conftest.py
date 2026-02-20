"""Shared test fixtures for meganova-mcp-server."""

from __future__ import annotations

import pytest

from meganova_mcp_server.config import Config


@pytest.fixture
def config() -> Config:
    """Provide a test Config with dummy values."""
    return Config(
        nova_mesh_url="http://localhost:8000",
        api_key="test-key-123",
    )
