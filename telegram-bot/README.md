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

## License

MIT
