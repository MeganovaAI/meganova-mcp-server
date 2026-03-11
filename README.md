# meganova-mcp-server

MCP server for [MegaNova AI](https://meganova.ai) — expose LLM inference, image/video generation, embeddings, cloud agents, and Nova Mesh routing to any MCP-compatible client (Claude Desktop, Cursor, VS Code, Windsurf, etc.).

## What It Does

| MCP Primitive | Capabilities |
|---------------|-------------|
| **Tools — Inference** | `chat_completion`, `create_embeddings`, `rerank_documents` |
| **Tools — Media** | `generate_image`, `generate_video`, `transcribe_audio` |
| **Tools — Models** | `list_models` (with filtering by modality, family, use case) |
| **Tools — Cloud Agents** | `cloud_agent_info`, `cloud_agent_chat`, `cloud_agent_confirm_tool` |
| **Tools — Nova Mesh** | `route_task`, `chat_with_agent`, `list_agents`, `get_agent_info`, `execute_dag`, `get_call_log` |
| **Tools — Skills** | `list_skills`, `execute_skill`, `search_catalog` |
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
export MEGANOVA_API_KEY=your-api-key                          # Required
export MEGANOVA_API_URL=https://api.meganova.ai/v1            # Default
export MEGANOVA_STUDIO_URL=https://studio-api.meganova.ai     # Default
export NOVA_MESH_URL=https://your-mesh-endpoint               # Optional, for mesh tools
```

### Run (stdio)

```bash
meganova-mcp-server
```

### Run (HTTP)

```bash
MCP_TRANSPORT=http MCP_PORT=8080 meganova-mcp-server
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
        "MEGANOVA_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Cursor / Windsurf

Use the HTTP transport and point to `http://localhost:8080/mcp`.

## Tool Reference

### Inference

- **`chat_completion`** — Send messages to any MegaNova LLM (Manta, Qwen, Gemini, Deepseek, etc.)
- **`create_embeddings`** — Generate text embeddings for semantic search and RAG
- **`rerank_documents`** — Rerank documents by relevance to a query

### Media

- **`generate_image`** — Text-to-image with FLUX, SeedDream, and other models
- **`generate_video`** — Text-to-video generation
- **`transcribe_audio`** — Audio-to-text transcription from URL

### Model Discovery

- **`list_models`** — Browse available models with filters (modality, family, pricing)

### Cloud Agents

- **`cloud_agent_info`** — Get info about a deployed Studio agent
- **`cloud_agent_chat`** — Chat with a deployed agent (supports multi-turn conversations)
- **`cloud_agent_confirm_tool`** — Approve or reject pending agent tool calls

### Nova Mesh

- **`route_task`** — Auto-route tasks to the best agent in the mesh
- **`chat_with_agent`** — Direct message to a specific mesh agent
- **`list_agents`** / **`get_agent_info`** — Discover mesh agents
- **`execute_dag`** — Run multi-step DAG execution plans
- **`get_call_log`** — View recent LLM call history

### Skills

- **`list_skills`** / **`search_catalog`** — Discover available skill packs
- **`execute_skill`** — Run a specific tool from a skill pack

## Docker

```bash
docker build -t meganova-mcp-server .
docker run -e MEGANOVA_API_KEY=key -p 8080:8080 meganova-mcp-server
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
