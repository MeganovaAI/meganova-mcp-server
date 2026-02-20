"""FastMCP server instance with tool, resource, and prompt registration."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from meganova_mcp_server.config import load_config


def create_server() -> FastMCP:
    """Create and configure the MCP server with all tools, resources, and prompts."""
    config = load_config()

    mcp = FastMCP(
        name=config.server_name,
        version=config.server_version,
    )

    # Register tool modules
    from meganova_mcp_server.tools.agents import register as register_agents
    from meganova_mcp_server.tools.routing import register as register_routing
    from meganova_mcp_server.tools.skills import register as register_skills

    register_agents(mcp, config)
    register_skills(mcp, config)
    register_routing(mcp, config)

    # Register resource modules
    from meganova_mcp_server.resources.agents import register as register_agent_resources

    register_agent_resources(mcp, config)

    # Register prompt modules
    from meganova_mcp_server.prompts.personas import register as register_persona_prompts

    register_persona_prompts(mcp, config)

    return mcp


def main() -> None:
    """Run the MCP server."""
    config = load_config()
    mcp = create_server()

    if config.transport == "http":
        mcp.run(transport="streamable-http", host=config.host, port=config.port)
    else:
        mcp.run(transport="stdio")
