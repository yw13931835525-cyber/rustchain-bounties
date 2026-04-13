# RustChain Telegram Bot — @RustChainBot

**Bounty:** #2869 | **Reward:** 10 RTC

A Telegram bot that lets users check their RustChain wallet balance, miner status, epoch info, and RTC price.

## Commands

| Command | Description |
|---------|-------------|
| `/balance <wallet>` | Check RTC balance for a wallet address |
| `/miners` | List active miners on the network |
| `/epoch` | Current epoch information |
| `/price` | RTC reference rate ($0.10 USD) |
| `/help` | Show all commands |

## Rate Limiting

- 1 request per 5 seconds per user
- Prevents abuse and reduces load on public RPC nodes

## Setup

### 1. Get a Telegram Bot Token

1. Open Telegram and chat with [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow the prompts — give it a name and username
4. Copy the token it gives you

### 2. Clone & Install

```bash
git clone https://github.com/Scottcjn/rustchain-bounties.git
cd rustchain-bounties/telegram-bot
pip install -r requirements.txt
```

### 3. Configure

Create a `.env` file:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
RPC_URL=https://50.28.86.131
```

### 4. Run

```bash
python bot.py
```

---

## Deployment Options

### Option A — systemd (Linux server)

```bash
sudo cp rustchain-telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rustchain-telegram-bot
sudo systemctl start rustchain-telegram-bot
```

Edit the token in the service file first, or override via environment:

```bash
TELEGRAM_BOT_TOKEN=your_token sudo systemctl start rustchain-telegram-bot
```

### Option B — Docker

```bash
docker build -t rustchain-telegram-bot .
docker run -d \
  --name rustchain-telegram-bot \
  --env TELEGRAM_BOT_TOKEN=your_token \
  rustchain-telegram-bot
```

Or with docker-compose:

```bash
echo "TELEGRAM_BOT_TOKEN=your_token" > .env
docker-compose up -d
```

### Option C — Railway

1. Push this directory to a GitHub repo
2. Connect to [Railway](https://railway.app)
3. Add the `TELEGRAM_BOT_TOKEN` environment variable
4. Deploy — Railway auto-detects Python

### Option D — Fly.io

```bash
fly launch
fly secrets set TELEGRAM_BOT_TOKEN=your_token
fly deploy
```

---

## Error Handling

- If the RPC node is unreachable, the bot replies with "❌ Node unreachable"
- Invalid wallet addresses return a usage hint
- Rate-limited users see a countdown before they can try again

## File Structure

```
telegram-bot/
├── bot.py                    # Main bot logic
├── config.py                 # Configuration & env loading
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container build
├── docker-compose.yml        # Docker Compose setup
├── rustchain-telegram-bot.service  # systemd unit
└── README.md                 # This file
```

## RTC Wallet for Bounty Payment

- **Network:** EVM-compatible
- **Address:** `0x6FCBd5d14FB296933A4f5a515933B153bA24370E`

## License

MIT — see repository root.
