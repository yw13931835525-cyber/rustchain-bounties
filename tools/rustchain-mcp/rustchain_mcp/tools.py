"""RustChain MCP tools — exposed to any MCP-compatible AI agent."""

from typing import Any

from .client import get_client


# ── Tool schemas ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "rustchain_health",
        "description": "Check RustChain node health status. Returns version, uptime, DB read-write mode, and chain tip age.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "rustchain_balance",
        "description": "Query RTC wallet balance by wallet address or miner ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "RTC wallet address (e.g. RTCxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx).",
                },
                "miner_id": {
                    "type": "string",
                    "description": "Miner ID (alternative to address).",
                },
            },
            "propertiesOrder": ["address", "miner_id"],
        },
    },
    {
        "name": "rustchain_miners",
        "description": "List all active miners on the RustChain network.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "rustchain_epoch",
        "description": "Get current epoch number, start/end times, and rewards info.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "rustchain_wallet_history",
        "description": "Get transaction history for a wallet address.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "RTC wallet address.",
                    "minLength": 10,
                },
                "limit": {
                    "type": "integer",
                    "description": "Max transactions to return (default 50, max 200).",
                    "default": 50,
                },
            },
            "required": ["address"],
        },
    },
    {
        "name": "rustchain_attestation_status",
        "description": "Get attestation status for a miner public key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "miner_public_key": {
                    "type": "string",
                    "description": "Miners public key (base58 or hex).",
                },
            },
            "required": ["miner_public_key"],
        },
    },
    {
        "name": "rustchain_explorer_blocks",
        "description": "Get recent blocks from the RustChain explorer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of blocks to return (default 20, max 100).",
                    "default": 20,
                },
            },
        },
    },
    {
        "name": "rustchain_explorer_transactions",
        "description": "Get transactions from the RustChain explorer, optionally filtered by wallet address.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Wallet address to filter by (optional).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of transactions to return (default 20, max 100).",
                    "default": 20,
                },
            },
        },
    },
    {
        "name": "rustchain_governance_proposals",
        "description": "List RustChain governance proposals, optionally filtered by status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status: active, passed, rejected, executed (optional).",
                    "enum": ["active", "passed", "rejected", "executed"],
                },
            },
        },
    },
]


# ── Tool handlers ─────────────────────────────────────────────────────────────

def handle_rustchain_health(arguments: dict) -> dict:
    client = get_client()
    return client.health()


def handle_rustchain_balance(arguments: dict) -> dict:
    client = get_client()
    address = arguments.get("address")
    miner_id = arguments.get("miner_id")
    if address:
        return client.balance(address)
    if miner_id:
        return client.balance_by_miner_id(miner_id)
    return {"error": "Either 'address' or 'miner_id' is required."}


def handle_rustchain_miners(arguments: dict) -> dict:
    client = get_client()
    return {"miners": client.miners()}


def handle_rustchain_epoch(arguments: dict) -> dict:
    client = get_client()
    return client.epoch()


def handle_rustchain_wallet_history(arguments: dict) -> dict:
    client = get_client()
    return client.wallet_history(
        address=arguments["address"],
        limit=min(arguments.get("limit", 50), 200),
    )


def handle_rustchain_attestation_status(arguments: dict) -> dict:
    client = get_client()
    return client.attestation_status(arguments["miner_public_key"])


def handle_rustchain_explorer_blocks(arguments: dict) -> dict:
    client = get_client()
    return {"blocks": client.explorer_blocks(limit=min(arguments.get("limit", 20), 100))}


def handle_rustchain_explorer_transactions(arguments: dict) -> dict:
    client = get_client()
    return {
        "transactions": client.explorer_transactions(
            address=arguments.get("address"),
            limit=min(arguments.get("limit", 20), 100),
        )
    }


def handle_rustchain_governance_proposals(arguments: dict) -> dict:
    client = get_client()
    return {"proposals": client.governance_proposals(status=arguments.get("status"))}


HANDLERS = {
    "rustchain_health": handle_rustchain_health,
    "rustchain_balance": handle_rustchain_balance,
    "rustchain_miners": handle_rustchain_miners,
    "rustchain_epoch": handle_rustchain_epoch,
    "rustchain_wallet_history": handle_rustchain_wallet_history,
    "rustchain_attestation_status": handle_rustchain_attestation_status,
    "rustchain_explorer_blocks": handle_rustchain_explorer_blocks,
    "rustchain_explorer_transactions": handle_rustchain_explorer_transactions,
    "rustchain_governance_proposals": handle_rustchain_governance_proposals,
}
