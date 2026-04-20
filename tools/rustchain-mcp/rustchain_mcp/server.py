"""
RustChain MCP Server — Model Context Protocol server for RustChain.

Exposes RustChain node operations as MCP tools to any MCP-compatible AI agent
(Claude Code, Cursor, Windsurf, VS Code Copilot, etc.).

Usage:
    # Run directly with Python
    python -m rustchain_mcp.server

    # Run with uvx (no install needed)
    uvx rustchain-mcp

    # Or install and run
    pip install rustchain-mcp
    rustchain-mcp
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# MCP SDK — support both v1 (legacy) and newer versions
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    from mcp.server import InitializationOptions
    MCP_V1 = True
except ImportError:
    try:
        from mcp import Server, stdio_server, Tool, TextContent
        from mcp.server import InitializationOptions
        MCP_V1 = True
    except ImportError:
        MCP_V1 = False

from .tools import TOOLS, HANDLERS

# Server instance name
SERVER_NAME = "rustchain-mcp"
SERVER_VERSION = "0.1.0"


def get_tools():
    """Convert our tool schemas to MCP Tool objects."""
    if MCP_V1:
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"],
            )
            for t in TOOLS
        ]
    # Fallback: return raw dicts for experimental MCP versions
    return [Tool(**t) for t in TOOLS]


async def main():
    """Start the MCP server."""
    if not MCP_V1:
        print(
            "ERROR: mcp package not found. Install with: pip install 'mcp>=1.0.0'",
            file=sys.stderr,
        )
        sys.exit(1)

    server = Server(SERVER_NAME)

    @server.list_tools()
    async def list_tools():
        """Return all RustChain tools."""
        return get_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Handle a tool call request."""
        handler = HANDLERS.get(name)
        if not handler:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        try:
            result = handler(arguments)
            return [TextContent(type="text", text=_fmt(result))]
        except Exception as e:
            logger.exception("Tool %s failed", name)
            return [TextContent(type="text", text=f"Error: {e}")]

    # Read node URL from env (optional override)
    node_url = os.environ.get("RUSTCHAIN_NODE_URL")
    if node_url:
        logger.info("Using node URL from RUSTCHAIN_NODE_URL: %s", node_url)
    else:
        logger.info("Using default node URL: https://50.28.86.131")

    options = InitializationOptions(
        server_name=SERVER_NAME,
        server_version=SERVER_VERSION,
        tcp_server_port=None,
        next_websocket_url=None,
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


def _fmt(data) -> str:
    """Format result as readable string."""
    import json
    try:
        return json.dumps(data, indent=2, default=str)
    except Exception:
        return str(data)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
