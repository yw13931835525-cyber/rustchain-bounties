# RustChain Development Tools

A VS Code extension for RustChain development — providing real-time wallet monitoring, miner status, epoch countdown, and bounty browsing.

## Features

### Status Bar Items

| Item | Position | Description |
|------|----------|-------------|
| **RTC Balance** | Right | Shows your RTC wallet balance. Click to set wallet ID. |
| **Miner Status** | Right | Green/red indicator — shows whether your miner is actively attesting. |
| **Epoch Timer** | Left | Live countdown to the next RustChain epoch (mm:ss format). |

### Bounty Browser (Sidebar)

Open the **RustChain Bounties** view in the Activity Bar to browse open bounties from the [rustchain-bounties](https://github.com/Scottcjn/rustchain-bounties) repository.

- Click any bounty to open it in your browser.
- Use **Refresh** to re-fetch the latest bounty list.
- Use **Claim Bounty** to open a pre-filled PR template for the selected issue.

### Commands

| Command | Description |
|---------|-------------|
| `RustChain: Refresh RTC Balance` | Manually refresh the balance status bar |
| `RustChain: Refresh Miner Status` | Manually refresh the miner status indicator |
| `RustChain: Set Miner/Wallet ID` | Configure your wallet/miner ID |
| `RustChain: Check Node Health` | Show node health and epoch info |
| `RustChain: Refresh Bounty List` | Refresh the bounty browser |
| `RustChain: Claim Bounty` | Claim a bounty (opens PR template) |

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `rustchain.nodeUrl` | `https://50.28.86.131` | RustChain node URL |
| `rustchain.minerId` | _(empty)_ | Your miner/wallet ID (e.g. `hebeigaoruan-rtc`) |
| `rustchain.balanceRefreshInterval` | `120` seconds | Balance refresh rate |
| `rustchain.minerRefreshInterval` | `60` seconds | Miner status refresh rate |
| `rustchain.showBalance` | `true` | Toggle balance display |
| `rustchain.rejectUnauthorized` | `false` | Enforce TLS cert validation |

## Requirements

- VS Code 1.80.0 or later

## Extension Architecture

```
src/
  extension.ts       — Entry point, wires up all components
  rustchainApi.ts    — HTTP client for RustChain node & GitHub API
  balanceStatusBar.ts — RTC balance status bar item
  minerStatus.ts     — Miner attesting status (green/red)
  epochTimer.ts      — Live epoch countdown
  nodeHealth.ts      — Node health check command
  bountyBrowser.ts   — Sidebar bounty tree view
```

## API Endpoints Used

- `GET /wallet/balance?miner_id=<id>` — RTC wallet balance
- `GET /api/miners` — Miner list with attesting status
- `GET /epoch` — Current epoch info
- `GET /health` — Node health
- `GET api.github.com/repos/Scottcjn/rustchain-bounties/issues` — Open bounties

## Bounty

This extension was developed for [RustChain Bounty #2868](https://github.com/Scottcjn/rustchain-bounties/issues/2868).

**Wallet:** `hebeigaoruan-rtc`
