# RustChain MCP Server

Connect any AI agent (Claude Code, Cursor, Windsurf, VS Code Copilot, etc.) to RustChain via the Model Context Protocol.

## Tools

| Tool | Description |
|------|-------------|
| `rustchain_health` | Node health, version, uptime, DB status |
| `rustchain_balance` | Wallet balance by address or miner ID |
| `rustchain_miners` | List active miners |
| `rustchain_epoch` | Current epoch info |
| `rustchain_wallet_history` | Transaction history for a wallet |
| `rustchain_attestation_status` | Attestation status for a miner |
| `rustchain_explorer_blocks` | Recent blocks |
| `rustchain_explorer_transactions` | Transactions (optionally by address) |
| `rustchain_governance_proposals` | Governance proposals |

## Install

### Option 1 — pip (published package)
```bash
pip install rustchain-mcp
rustchain-mcp
```

### Option 2 — uvx (no install)
```bash
uvx rustchain-mcp
```

### Option 3 — Clone + dev install
```bash
git clone https://github.com/Scottcjn/rustchain-bounties.git
cd rustchain-bounties/tools/rustchain-mcp
pip install -e .
rustchain-mcp
```

## Claude Code Setup

Add to your Claude Code MCP settings (`~/.claude/settings.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "rustchain": {
      "command": "uvx",
      "args": ["rustchain-mcp"]
    }
  }
}
```

Or with a custom node URL:

```json
{
  "mcpServers": {
    "rustchain": {
      "command": "uvx",
      "args": ["rustchain-mcp"],
      "env": {
        "RUSTCHAIN_NODE_URL": "https://50.28.86.131"
      }
    }
  }
}
```

## Cursor / Windsurf / Other MCP Clients

```json
{
  "mcpServers": {
    "rustchain": {
      "command": "uvx",
      "args": ["rustchain-mcp"]
    }
  }
}
```

## Usage Example (Claude Code)

Once configured, Claude Code can query RustChain directly:

```
rustchain_health — is the node online?
rustchain_balance — check my wallet balance
rustchain_epoch — what epoch are we in?
rustchain_miners — how many active miners?
```

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `RUSTCHAIN_NODE_URL` | `https://50.28.86.131` | RustChain node RPC URL |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
