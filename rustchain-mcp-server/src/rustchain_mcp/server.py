"""
RustChain MCP Server — Exposes RustChain as MCP tools for AI agents
Compatible with Claude Code, Cursor, Windsurf, VS Code Copilot MCP
"""

import os
import httpx
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Configuration
NODE_URL = os.environ.get("RUSTCHAIN_NODE_URL", "https://50.28.86.131")
PORT = int(os.environ.get("RUSTCHAIN_MCP_PORT", "8080"))

# Initialize server
server = Server("rustchain-mcp")


def _get_client() -> httpx.Client:
    return httpx.Client(base_url=NODE_URL, timeout=30.0)


# ─── Tools ────────────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="rustchain_health",
            description="Check RustChain node health status",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="rustchain_balance",
            description="Query RTC wallet balance for a given wallet name",
            inputSchema={
                "type": "object",
                "required": ["wallet_name"],
                "properties": {
                    "wallet_name": {"type": "string", "description": "Wallet name to query"},
                },
            },
        ),
        Tool(
            name="rustchain_miners",
            description="List all active miners and their status",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="rustchain_epoch",
            description="Get current epoch number and progress",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="rustchain_create_wallet",
            description="Register a new wallet for an AI agent on RustChain",
            inputSchema={
                "type": "object",
                "required": ["wallet_name"],
                "properties": {
                    "wallet_name": {"type": "string", "description": "Desired wallet name"},
                },
            },
        ),
        Tool(
            name="rustchain_submit_attestation",
            description="Submit a hardware fingerprint attestation",
            inputSchema={
                "type": "object",
                "required": ["wallet_name", "fingerprint"],
                "properties": {
                    "wallet_name": {"type": "string", "description": "Wallet name submitting attestation"},
                    "fingerprint": {"type": "string", "description": "Hardware fingerprint hash"},
                },
            },
        ),
        Tool(
            name="rustchain_bounties",
            description="List all open bounties on RustChain",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_reward": {"type": "number", "description": "Filter: minimum reward amount"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    client = _get_client()

    try:
        if name == "rustchain_health":
            r = client.get("/health")
            r.raise_for_status()
            data = r.json()
            return [TextContent(type="text", text=f"✅ RustChain Node Healthy\n"
                f"Block Height: {data.get('block_height', 'N/A')}\n"
                f"Peers: {data.get('peers', 'N/A')}\n"
                f"Status: {data.get('status', 'ok')}")]

        elif name == "rustchain_balance":
            wallet = arguments["wallet_name"]
            r = client.get(f"/wallet/balance", params={"wallet_id": wallet})
            r.raise_for_status()
            data = r.json()
            balance = data.get("balance", 0)
            return [TextContent(type="text", text=f"💰 Wallet: {wallet}\nBalance: {balance} RTC")]

        elif name == "rustchain_miners":
            r = client.get("/api/miners")
            r.raise_for_status()
            miners = r.json()
            lines = ["⛏️ Active Miners:"]
            for m in miners[:10]:
                status = "🟢 attesting" if m.get("attesting") else "🔴 offline"
                lines.append(f"  {m.get('id', '?')} — {status} (power: {m.get('power', '?')})")
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "rustchain_epoch":
            r = client.get("/epoch")
            r.raise_for_status()
            data = r.json()
            return [TextContent(type="text", text=f"📊 Epoch: {data.get('epoch', '?')}\n"
                f"Progress: {data.get('progress', '?')}%\n"
                f"Next settlement: {data.get('next_settlement', '?')}")]

        elif name == "rustchain_create_wallet":
            wallet = arguments["wallet_name"]
            r = client.post("/wallet/create", json={"wallet_name": wallet})
            r.raise_for_status()
            data = r.json()
            return [TextContent(type="text", text=f"✅ Wallet created: {wallet}\n"
                f"Address: {data.get('address', 'N/A')}")]

        elif name == "rustchain_submit_attestation":
            wallet = arguments["wallet_name"]
            fingerprint = arguments["fingerprint"]
            r = client.post("/attestation/submit", json={
                "wallet_name": wallet,
                "fingerprint": fingerprint,
            })
            r.raise_for_status()
            data = r.json()
            return [TextContent(type="text", text=f"✅ Attestation submitted\n"
                f"Wallet: {wallet}\n"
                f"Fingerprint: {fingerprint}\n"
                f"Status: {data.get('status', 'accepted')}")]

        elif name == "rustchain_bounties":
            min_reward = arguments.get("min_reward", 0)
            r = httpx.get(
                "https://api.github.com/repos/Scottcjn/rustchain-bounties/issues",
                params={"state": "open", "labels": "bounty", "per_page": "50"},
                headers={"Accept": "application/vnd.github+json"},
                timeout=15.0,
            )
            r.raise_for_status()
            issues = r.json()
            lines = ["🎯 Open Bounties:"]
            count = 0
            for issue in issues:
                reward = issue.get("title", "").split("]")[0] + "]"
                if any(str(min_reward) in t for t in [issue.get("title", "")]):
                    lines.append(f"  #{issue['number']} — {issue['title'][:60]}")
                    count += 1
            lines.append(f"\nTotal: {len(issues)} open bounties")
            return [TextContent(type="text", text="\n".join(lines))]

        else:
            return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]

    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=f"❌ HTTP error {e.response.status_code}: {e.response.text}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
    finally:
        client.close()


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
