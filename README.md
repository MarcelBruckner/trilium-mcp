# Trilium ETAPI MCP server

A standalone [MCP](https://modelcontextprotocol.io) server that exposes the
[Trilium](https://triliumnotes.org) [ETAPI](https://github.com/TriliumNext/Trilium)
(External API) as MCP tools. It runs as a **container sidecar** next to your Trilium
instance: every documented ETAPI endpoint is turned into an MCP tool at startup via
`FastMCP.from_openapi` (currently **40 tools** — `createNote`, `getNoteById`,
`searchNotes`, `exportNoteSubtree`, …), served over streamable **HTTP** so any MCP
client connects to it by URL.

## Architecture

```
MCP client (Claude Code, …)  ──HTTP /mcp──▶  mcp sidecar  ──ETAPI──▶  trilium
                                             (this repo)   http://trilium:8080/etapi
```

The sidecar talks to Trilium over the internal Docker network, so Trilium's ETAPI is
never exposed publicly on its own.

## Setup

1. **Create an ETAPI token** in Trilium: *Options → ETAPI → Create new ETAPI token*.
   This token is the only credential — the server itself stores no secret. Each
   client presents its own token per request as `Authorization: Bearer <token>`,
   and the server forwards the raw token straight through to Trilium's ETAPI.
2. **Configure** the deployment via environment variables (see Configuration below) —
   at minimum `TRILIUM_SERVER_URL` pointing at your Trilium instance.
3. **Run** both Trilium and the sidecar:
   ```
   docker compose up -d --build
   ```
   The MCP endpoint is then available at `http://localhost:8081/mcp`.

## Connecting a client

The ETAPI token you create in Trilium (Options → ETAPI) is the credential — pass it as
a bearer header:

```bash
claude mcp add trilium --transport http \
  --header "Authorization: Bearer YOUR_TRILIUM_ETAPI_TOKEN" \
  https://your-host/mcp
```

Register multiple instances by repeating with a different URL + token:

```bash
claude mcp add trilium-work --transport http \
  --header "Authorization: Bearer WORK_TOKEN" \
  https://work-host/mcp
```

All of them use the same trilium-mcp image; each deployment is bound to one Trilium via
`TRILIUM_SERVER_URL`.

Alternatively, use the provided [`.mcp.json`](.mcp.json), filling in your host and token.

## TLS / reverse proxy

The container serves plain HTTP on `:8081`; terminate TLS at your reverse proxy.
Example Caddyfile:

```
your-host {
    reverse_proxy mcp:8081
}
```

## Configuration

All configuration is via environment variables:

| Variable             | Default               | Purpose                                                                |
| -------------------- | --------------------- | ---------------------------------------------------------------------- |
| `TRILIUM_SERVER_URL` | `http://trilium:8080` | Base URL of the Trilium instance (`/etapi` is appended automatically). |
| `MCP_HOST`           | `0.0.0.0`             | Interface the MCP server binds to.                                     |
| `MCP_PORT`           | `8081`                | Port the MCP server listens on.                                        |
| `MCP_PATH`           | `/mcp`                | HTTP path the MCP endpoint is served at.                               |
| `TRILIUM_ETAPI_SPEC` | bundled spec          | Override the OpenAPI spec path.                                        |

## Security

The MCP endpoint grants **full read/write access to your notes**. Every request must
carry a valid Trilium ETAPI token in the `Authorization` header; requests with no
`Authorization` header at all are rejected with `401` before reaching any tool. The
server never validates the token itself — validity is enforced by Trilium when the
forwarded request reaches the actual ETAPI call, and the server holds no secret of its
own. The `/health` endpoint is always unauthenticated (used by the container
healthcheck).

Because the token is forwarded as-is on every call, only run this behind TLS: put the
Caddy (or other) reverse proxy in front and let it terminate TLS, so the token never
travels over plain HTTP outside the trusted Docker network.

If the OpenAPI spec cannot be loaded at startup, the server still starts and completes
the MCP handshake, but exposes only a single `startup_error` tool describing how to fix
it (rather than failing with an opaque connection error).

## Layout

```
docker-compose.yaml      trilium + mcp sidecar
Dockerfile               builds the MCP server image (uv-based)
.mcp.json                example MCP client config
app/
  server.py              the MCP server (OpenAPI-driven, HTTP transport, token pass-through)
  pyproject.toml         dependencies
  uv.lock
  trillium-etapi.openapi bundled Trilium ETAPI OpenAPI spec
```
