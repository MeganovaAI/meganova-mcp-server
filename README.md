# meganova-mcp-server

MCP server for [Nova Mesh](https://meganova.ai) — expose agent routing, skill execution, and observability to any MCP-compatible client (Claude Desktop, Cursor, Windsurf, etc.).

## What It Does

| MCP Primitive | Capabilities |
|---------------|-------------|
| **Tools** | `route_task`, `chat_with_agent`, `list_agents`, `get_agent_info`, `list_skills`, `execute_skill`, `search_catalog`, `execute_dag`, `get_call_log` |
| **Resources** | `nova://agents` (index), `nova://agents/{name}` (profile) |
| **Prompts** | `route_task_prompt`, `agent_chat_prompt`, `skill_discovery_prompt` |

## Quick Start

### Install

```bash
pip install meganova-mcp-server
```

Or from source:

```bash
git clone https://github.com/MeganovaAI/meganova-mcp-server.git
cd meganova-mcp-server
pip install -e .
```

### Configure

Set environment variables:

```bash
export NOVA_MESH_URL=https://api.meganova.ai   # Your Nova Mesh endpoint
export MEGANOVA_API_KEY=your-api-key            # Your API key
```

### Run (stdio)

```bash
meganova-mcp-server
```

### Run (HTTP)

```bash
TRANSPORT=http PORT=8080 meganova-mcp-server
```

## Client Setup

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "meganova": {
      "command": "meganova-mcp-server",
      "env": {
        "NOVA_MESH_URL": "https://api.meganova.ai",
        "MEGANOVA_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Claude Code

Add to `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "meganova": {
      "command": "meganova-mcp-server",
      "env": {
        "NOVA_MESH_URL": "https://api.meganova.ai",
        "MEGANOVA_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Cursor / Windsurf

Use the HTTP transport and point to `http://localhost:8080/mcp`.

## Docker

```bash
docker build -t meganova-mcp-server .
docker run -e NOVA_MESH_URL=https://api.meganova.ai -e MEGANOVA_API_KEY=key -p 8080:8080 meganova-mcp-server
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
