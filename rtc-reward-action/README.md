# rtc-reward-action

> Automatically award **RTC tokens** when a PR is merged.

## Usage

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
          node-url: 'https://50.28.86.131'
          amount: '5'
          wallet-from: 'your-project-wallet'
          dry-run: 'false'
        env:
          ADMIN_KEY: ${{ secrets.RTC_ADMIN_KEY }}
```

## PR authors

Add your wallet to the PR description:

```
wallet: your_rtc_wallet_name
```

## Features

- Reads wallet from PR body
- Posts confirmation comment on PR
- Dry-run mode supported
- GitHub Marketplace ready

## License

MIT
