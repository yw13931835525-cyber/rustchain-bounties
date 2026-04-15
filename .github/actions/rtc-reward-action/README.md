# RTC Reward GitHub Action

A reusable GitHub Action that **automatically awards RTC tokens** to contributors when their pull requests are merged.

## Features

- ✅ Configurable RTC amount per merge
- ✅ Reads contributor wallet from PR body or falls back to GitHub username
- ✅ Posts confirmation comment on PR after payment
- ✅ Dry-run mode for testing
- ✅ Reusable — add one YAML file to any repo
- ✅ Published to GitHub Marketplace

## Usage

### 1. Get your admin wallet key

Generate an admin wallet on RustChain and fund it with RTC for rewards.

### 2. Add the action to your repo

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
          node-url: "https://50.28.86.131"
          amount: "5"
          wallet-name: "your-project-wallet"
          admin-key: ${{ secrets.RTC_ADMIN_KEY }}
          dry-run: "false"
```

### 3. Add the secret

Go to **Settings → Secrets → Actions** and add:
- `RTC_ADMIN_KEY` — your admin wallet private key

## Wallet Extraction

The action looks for the contributor's wallet in this order:

1. **PR body** — looks for patterns like `wallet: <name>` or `rtc-wallet: <name>`
2. **Fallback** — uses the contributor's GitHub username as their wallet name

Encourage contributors to add their wallet in the PR description:
```
Wallet: my-rtc-wallet-name
```

## Example

```yaml
# Full example with all options
- uses: Scottcjn/rtc-reward-action@v1
  with:
    node-url: "https://50.28.86.131"
    amount: "10"
    wallet-name: "bounty-fund"
    admin-key: ${{ secrets.RTC_ADMIN_KEY }}
    dry-run: "false"
```

## License

MIT
