# RustChain Telegram Bot

**Bounty:** #2869  
**Reward:** 10 RTC  
**Created:** 2026-04-13  

## 🤖 About

A Telegram bot that checks your RustChain wallet balance and miner status.

## 💼 Company Info

- **Company:** 河北高软科技有限公司  
- **Wallet:** 0x6FCBd5d14FB296933A4f5a515933B153bA24370E  

## 🚀 Quick Start

### 1. Create Bot

```bash
# Go to https://t.me/BotFather
# /newbot command
# Copy the token
```

### 2. Setup

```bash
# Save token in .env
echo "BOT_TOKEN=your_token_here" > .env

# Install dependencies
pip install telebot python-dotenv

# Run bot
python rustchain-telegram-bot.py
```

### 3. Add to Groups

```bash
# /addbottongroup
# Choose your group
# Confirm addition
```

## 💬 Commands

| Command | Description |
|---------|-----|
| `/start` | Welcome message |
| `/balance` | Check wallet balance |
| `/miner` | Check miner status |
| `/block <num>` | View block info |

## 📊 Features

- ✅ Real-time balance checking
- ✅ Miner status monitoring
- ✅ Block information display
- ✅ Group support
- ✅ Error handling

## 🔧 Configuration

Edit `rustchain-telegram-bot.py`:

```python
BOT_TOKEN = "your_token"  # From BotFather
WALLET_ADDRESS = "0x..."  # Your wallet
RUSTCHAIN_API = "..."     # API endpoint
```

## 📝 License

MIT License

## 🏢 Submitted by

河北高软科技有限公司  
Wallet: 0x6FCBd5d14FB296933A4f5a515933B153bA24370E  
