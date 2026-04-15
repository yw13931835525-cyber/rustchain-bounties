# RustChain MCP Server

Connect any AI agent (Claude Code, Cursor, Windsurf, VS Code Copilot) to RustChain blockchain.

## Install

```bash
pip install rustchain-mcp
```

Or with uvx (no install needed):

```bash
uvx rustchain-mcp
```

## Configure Claude Code

Add to your Claude Code config (`~/.claude.json` or project `.mcp.json`):

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

Or for installed version:

```json
{
  "mcpServers": {
    "rustchain": {
      "command": "rustchain-mcp"
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `rustchain_health` | Check node health |
| `rustchain_balance` | Query wallet balance |
| `rustchain_miners` | List active miners |
| `rustchain_epoch` | Current epoch info |
| `rustchain_create_wallet` | Register new agent wallet |
| `rustchain_submit_attestation` | Submit hardware fingerprint |
| `rustchain_bounties` | List open bounties |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RUSTCHAIN_NODE_URL` | `https://50.28.86.131` | RustChain node URL |
| `RUSTCHAIN_MCP_PORT` | `8080` | MCP server port |

## Example Usage

```
> check my wallet balance
💰 Wallet: agent-001
Balance: 42.5 RTC

> list active miners
⛏️ Active Miners:
  miner_42 — 🟢 attesting (power: 100)
  miner_17 — 🔴 offline
  ...

> show open bounties
🎯 Open Bounties:
  #2867 — [BOUNTY: 100 RTC] Security Audit...
  #2868 — [BOUNTY: 30 RTC] VS Code Extension...
  ...
```

## License

MIT
