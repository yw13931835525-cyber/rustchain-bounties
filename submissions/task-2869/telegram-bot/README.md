# RustChain Telegram Bot

> Check wallet balance, miner status, and network info via Telegram.

## Commands

| Command | Description |
|---------|-------------|
| `/balance <wallet>` | Check RTC wallet balance |
| `/miners` | List active miners by antiquity |
| `/epoch` | Current epoch and node status |
| `/price` | RTC reference price |
| `/stats` | Quick network overview |
| `/help` | Show help |

## Quick Start

```bash
pip install -r requirements.txt
export BOT_TOKEN="your:botfather_token"
python bot.py
```

## Deploy

### Railway (free tier)
1. Fork this repo
2. Connect to Railway
3. Set BOT_TOKEN environment variable
4. Deploy

### Fly.io
```bash
fly launch
fly secrets set BOT_TOKEN="your:botfather_token"
fly deploy
```

### systemd (VPS)
```bash
sudo systemctl enable rustchain-bot
sudo systemctl start rustchain-bot
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| BOT_TOKEN | **required** | From @BotFather |
| NODE_URL | https://50.28.86.131 | RustChain node |

## Docker

```bash
docker build -t rustchain-bot .
docker run -d -e BOT_TOKEN="your:token" rustchain-bot
```

## RTC Wallet

`yw13931835525-cyber` (EVM: 0x6FCBd5d14FB296933A4f5a515933B153bA24370E)

## License

MIT
