# RTC Reward Action

A reusable GitHub Action that automatically awards **RTC tokens** to contributors when a Pull Request is merged.

Any open source project can add one YAML file and turn their repo into a crypto bounty platform.

---

## Features

- ✅ **Configurable RTC amount** per merge
- ✅ **Extracts contributor wallet** from PR body (EVM address, `wallet_name:` format, or backtick-wrapped)
- ✅ **Posts confirmation comment** on the PR after payment
- ✅ **Dry-run mode** for testing without spending tokens
- ✅ **Minimum PR body length** check to prevent spam
- ✅ **Idempotent** — updates existing reward comment instead of duplicating
- ✅ **Works as reusable action** — publish to GitHub Marketplace easily

---

## Quick Start

### 1. Add the Action to Your Workflow

Create `.github/workflows/rtc-reward.yml`:

```yaml
name: RTC Reward

on:
  pull_request:
    types: [closed]

jobs:
  reward:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: Scottcjn/rtc-reward-action@v1
        with:
          node-url: https://50.28.86.131
          amount: 5
          wallet-from: ${{ vars.RTC_FUND_WALLET }}
          admin-key: ${{ secrets.RTC_ADMIN_KEY }}
          dry-run: false
          min-body-length: 20
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Configure Secrets and Variables

In your GitHub repo settings:

| Setting | Name | Value |
|---------|------|-------|
| Secret | `RTC_ADMIN_KEY` | Your admin private key (64 hex chars) |
| Variable | `RTC_FUND_WALLET` | Sender wallet address (RTC...) |

### 3. Contributor Setup

Contributors add their EVM wallet address in the PR body. The action recognizes these formats:

**Format 1: Raw EVM address**
```
My PR changes...

EVM: 0x6FCBd5d14FB296933A4f5a515933B153bA24370E
```

**Format 2: `wallet_name:` prefix**
```
## My Contribution

wallet_name: 0x6FCBd5d14FB296933A4f5a515933B153bA24370E
```

**Format 3: Backtick-wrapped**
```
Payment: `0x6FCBd5d14FB296933A4f5a515933B153bA24370E`
```

> Minimum 20 characters in PR body required to qualify for reward.

---

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `node-url` | No | `https://50.28.86.131` | RTC node RPC URL |
| `amount` | No | `5` | RTC amount to award per merge |
| `wallet-from` | Yes | — | Sender wallet address |
| `admin-key` | Yes | — | Admin private key (64 hex) |
| `pr-number` | No | auto | PR number (auto-detected) |
| `dry-run` | No | `false` | Enable dry-run mode |
| `min-body-length` | No | `20` | Minimum PR body length |
| `repo-token` | Yes | — | GitHub token (use `${{ secrets.GITHUB_TOKEN }}`) |

---

## Outputs

| Output | Description |
|--------|-------------|
| `rewarded` | Whether reward was successfully processed |
| `recipient` | EVM wallet address of the contributor |
| `tx_hash` | Transaction hash of the RTC transfer |
| `amount` | Amount of RTC transferred |

---

## Dry-Run Mode

Enable dry-run to test the action without actual token transfers:

```yaml
with:
  dry-run: true
```

In dry-run mode, the action posts a simulated reward comment but does **not** submit any on-chain transaction.

---

## Publishing to GitHub Marketplace

1. **Tag a release** in your fork:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Create a release** on GitHub (Draft a new release → Publish release)

3. **Marketplace listing**: The action is auto-discoverable at:
   ```
   https://github.com/{owner}/{repo}/actions/{action-path}
   ```

4. **Marketplace URL** (after publishing):
   ```
   https://github.com/marketplace/actions/rtc-reward-action
   ```

---

## Example PR Reward Comment

After a successful reward, the action posts:

```
## 🎁 RTC Reward — PR #42

| Field | Value |
|-------|-------|
| 🧪 **Status** | ✅ Transfer successful |
| 💰 **Amount** | 5 RTC |
| 👛 **Recipient** | `0x6fcbd5d14fb296933a4f5a515933b153ba24370e` |
| 🔗 **TX Hash** | `0xabc123...` |
| 🤖 **Triggered by** | @contributor |

*Reward action — Run #1234*
```

---

## Architecture

```
.github/actions/rtc-reward-action/
├── action.yml       # Action definition (metadata + inputs/outputs)
├── entrypoint.sh    # Main execution script (bash + Python fallback)
└── README.md        # This file
```

The action uses:
- **Bash** for GitHub API calls and workflow orchestration
- **Python** (via inline script) for Ed25519 cryptographic signing
- **RPC node** for submitting signed transfers on-chain

---

## License

MIT — use freely for your crypto bounty platform.
