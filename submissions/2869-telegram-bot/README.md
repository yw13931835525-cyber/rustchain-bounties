# RustChain Telegram Bot — Bounty #2869

**Reward: 10 RTC**

A full-featured Telegram bot that lets users check their RustChain wallet balance, miner status, and network info.

## Commands

| Command | Description |
|---------|-------------|
| `/balance <miner_id>` | Check RTC wallet balance |
| `/miners` | List active miners |
| `/epoch` | Current epoch info |
| `/price` | Show RTC reference rate |
| `/stats` | Quick network overview |
| `/help` | Show help |

## Features

- ✅ All 5 required commands + bonus `/stats`
- ✅ Rate limiting (1 request / 5 seconds per user)
- ✅ Error handling for offline node
- ✅ Clean Markdown-formatted responses
- ✅ Works with python-telegram-bot v20+

## API Endpoints Used

```
GET https://50.28.86.131/health
GET https://50.28.86.131/wallet/balance?miner_id={name}
GET https://50.28.86.131/epoch
GET https://50.28.86.131/api/miners
```

## Setup

### 1. Install dependencies

```bash
pip install python-telegram-bot requests python-dotenv
```

### 2. Create a .env file

```bash
cp .env.example .env
# Edit .env and add your BOT_TOKEN
```

`.env.example`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
RUSTCHAIN_NODE_URL=https://50.28.86.131
```

### 3. Run locally

```bash
python bot.py
```

## Deploy

### Option A: Railway (recommended)

1. Push this directory to a GitHub repo
2. Connect to Railway (railway.app)
3. Add `TELEGRAM_BOT_TOKEN` environment variable
4. Railway auto-detects Python and deploys

**Railway `railway.toml`**:
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python bot.py"
```

### Option B: Fly.io

```bash
fly launch
fly secrets set TELEGRAM_BOT_TOKEN=your_token
fly deploy
```

### Option C: systemd (self-hosted VPS)

```ini
# /etc/systemd/system/rustchain-bot.service
[Unit]
Description=RustChain Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/rustchain-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always
Environment=TELEGRAM_BOT_TOKEN=your_token
Environment=RUSTCHAIN_NODE_URL=https://50.28.86.131

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable rustchain-bot
sudo systemctl start rustchain-bot
```

## Create Your Bot

1. Open Telegram and chat with [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow prompts (name, username)
4. Copy the token into your `.env` as `TELEGRAM_BOT_TOKEN`

## File Structure

```
submissions/2869-telegram-bot/
├── bot.py          # Main bot implementation
├── README.md       # This file
└── requirements.txt # Python dependencies
```

## Requirements

- Python 3.10+
- python-telegram-bot >= 20.0
- requests >= 2.28

## Wallet

RTC wallet name for payout: `hebeigaoruan-rtc`
