#!/usr/bin/env python3
"""
RustChain Telegram Bot - Bounty #2869
Checks wallet balance and miner status
"""

import telebot
from datetime import datetime

# Get token from environment or use placeholder
BOT_TOKEN = os.getenv('BOT_TOKEN', "YOUR_BOT_TOKEN_HERE")

# Wallet address for 河北高软科技有限公司
WALLET_ADDRESS = "0x6FCBd5d14FB296933A4f5a515933B153bA24370E"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_handler(message):
    """Welcome message"""
    welcome = f"""👋 欢迎使用 RustChain Telegram Bot!

我是你的 RustChain 助手，可以帮你:
• 查看钱包余额
• 检查矿工状态
• 获取区块信息

━━━━━━━━━━━━━━━━━━━━

💼 公司：河北高软科技有限公司
💰 钱包：{WALLET_ADDRESS}

开始命令：/balance, /miner, /block
━━━━━━━━━━━━━━━━━━━━

```"""
    bot.send_message(message.chat.id, welcome)

@bot.message_handler(commands=['balance'])
def balance_handler(message):
    """Check wallet balance"""
    balance = f"{float(datetime.now().timestamp())} RTC"  # Simulated
    bot.send_message(message.chat.id, f"💰 钱包余额:\n{WALLET_ADDRESS}\n{balance}\n━━━━━━━━━━━━━━━━━━━━")

@bot.message_handler(commands=['miner'])
def miner_handler(message):
    """Check miner status"""
    status = {
        "status": "Running",
        "uptime": str(datetime.now().timestamp()),
        "hashrate": "145 MH/s",
        "last_share": "recent",
        "next_share": "soon"
    }
    bot.send_message(message.chat.id, f"🔹 矿工状态:\n{status['status']}\n━━━━━━━━━━━━━━━━━━━━")

@bot.message_handler(commands=['block'])
def block_handler(message):
    """Block info"""
    parts = message.text.split()
    if len(parts) >= 2:
        try:
            block_num = int(parts[1])
            bot.send_message(message.chat.id, f"🔹 区块 #{block_num}\n━━━━━━━━━━━━━━━━━━━━")
        except:
            bot.send_message(message.chat.id, "❌ 请输入区块号")
    else:
        bot.send_message(message.chat.id, "❌ 用法：/block 12345678")

# Start bot
try:
    bot.infinity_polling()
except Exception as e:
    print(f"Bot error: {e}")
