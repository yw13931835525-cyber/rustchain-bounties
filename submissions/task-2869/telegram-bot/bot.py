#!/usr/bin/env python3
"""
RustChain Telegram Bot — @RustChainBot
Check wallet balance, miner status, and epoch info via Telegram.

Setup:
  1. Create a bot via @BotFather → get BOT_TOKEN
  2. pip install -r requirements.txt
  3. python bot.py

Deploy (Railway/Fly.io/systemd) — see README.md
"""

import os
import json
import time
import logging
from functools import wraps
from typing import Optional

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from telegram import Update
from telegram.ext import (
    Application, CommandHandler,
    ContextTypes, RateLimiter
)

# ── Config ──────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
NODE_URL  = os.environ.get("NODE_URL", "https://50.28.86.131")
RTC_PRICE = 0.10  # USD per RTC (reference rate)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Rate Limiter ─────────────────────────────────────────
# Simple per-user rate limiter: 1 request per 5 seconds
last_request: dict[int, float] = {}
RATE_LIMIT = 5.0  # seconds


def rate_limit(func):
    @wraps(func)
    async def wrapped(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        now = time.time()
        if user_id in last_request and (now - last_request[user_id]) < RATE_LIMIT:
            remaining = RATE_LIMIT - (now - last_request[user_id])
            await update.message.reply_text(
                f"⏳ Rate limit: please wait {remaining:.0f}s before the next command."
            )
            return
        last_request[user_id] = now
        return await func(update, ctx, *args, **kwargs)
    return wrapped


# ── Helpers ──────────────────────────────────────────────
def api_get(endpoint: str) -> Optional[dict]:
    """Fetch JSON from the RustChain node (self-signed cert)."""
    url = f"{NODE_URL}{endpoint}"
    try:
        r = requests.get(url, timeout=10, verify=False)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"API error {url}: {e}")
        return None


def fmt_rtc(amount: float) -> str:
    return f"{amount:,.4f} RTC"


# ── Commands ────────────────────────────────────────────
@rate_limit
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ *RustChain Bot* — Welcome!\n\n"
        "Track your RTC wallet and miner status right from Telegram.\n\n"
        "Commands:\n"
        "/balance <wallet> — Check wallet balance\n"
        "/miners — List active miners\n"
        "/epoch — Current epoch info\n"
        "/price — RTC price info\n"
        "/help — Show this message",
        parse_mode="Markdown"
    )


@rate_limit
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


@rate_limit
async def cmd_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            "Usage: /balance <wallet_name>\nExample: /balance nox-ventures"
        )
        return

    wallet = ctx.args[0].strip()
    await update.message.reply_text(
        f"🔍 Checking balance for `{wallet}`...", parse_mode="Markdown"
    )

    data = api_get(f"/api/balance/{wallet}")
    if data is None:
        await update.message.reply_text(
            "❌ Node unreachable or invalid wallet. Try again later."
        )
        return

    balance = data.get("balance", 0)
    addr    = data.get("address", wallet)
    usd     = balance * RTC_PRICE

    await update.message.reply_text(
        f"✅ *Wallet Balance*\n\n"
        f"👛 `{addr}`\n"
        f"💰 {fmt_rtc(balance)}\n"
        f"💵 ~${usd:.4f} USD\n\n"
        f"📊 Node: {NODE_URL}",
        parse_mode="Markdown"
    )


@rate_limit
async def cmd_miners(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛏ Fetching active miners...")

    data = api_get("/api/miners")
    if data is None:
        await update.message.reply_text(
            "❌ Node unreachable. Try again later."
        )
        return

    miners = data.get("miners", [])
    total  = data.get("pagination", {}).get("total", len(miners))
    miners.sort(key=lambda m: m.get("antiquity_multiplier", 0), reverse=True)

    lines = [f"⛏ *Active Miners* ({total} total)\n"]
    for i, m in enumerate(miners[:10], 1):
        mult = m.get("antiquity_multiplier", 0)
        hw   = m.get("hardware_type", "unknown")
        arch = m.get("device_arch", "")
        lines.append(f"{i}. `{m['miner']}`")
        lines.append(f"   ⚙ {hw} ({arch}) | ×{mult:.3f} antiquity")

    lines.append("\n_Showing top 10 by antiquity multiplier_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@rate_limit
async def cmd_epoch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Fetching epoch data...")

    health = api_get("/health")
    miners = api_get("/api/miners")

    if health is None:
        await update.message.reply_text(
            "❌ Node unreachable. Try again later."
        )
        return

    version   = health.get("version", "unknown")
    uptime_s  = health.get("uptime_s", 0)
    ok        = health.get("ok", False)
    uptime_h  = uptime_s / 3600
    miner_cnt = len(miners.get("miners", [])) if miners else 0

    status_emoji = "🟢" if ok else "🔴"
    await update.message.reply_text(
        f"📊 *Epoch / Node Status*\n\n"
        f"{status_emoji} Node: {'Online' if ok else 'Offline'}\n"
        f"🔧 Version: `{version}`\n"
        f"⏱ Uptime: {uptime_h:.1f} hours\n"
        f"⛏ Active miners: {miner_cnt}\n"
        f"🌐 Node: {NODE_URL}",
        parse_mode="Markdown"
    )


@rate_limit
async def cmd_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💲 *RTC Reference Price*\n\n"
        f"📌 {RTC_PRICE} USD per RTC\n\n"
        f"_Note: This is a reference rate. "
        f"Actual market price may vary. "
        f"Check DEX listings or RustChain official channels for live data._",
        parse_mode="Markdown"
    )


@rate_limit
async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Bonus: quick overview of network health."""
    health = api_get("/health")
    miners = api_get("/api/miners")

    if health is None:
        await update.message.reply_text("❌ Node unreachable.")
        return

    total_miners = len(miners.get("miners", [])) if miners else 0
    avg_mult = 0.0
    if miners:
        m_list = miners.get("miners", [])
        if m_list:
            avg_mult = sum(m.get("antiquity_multiplier", 0) for m in m_list) / len(m_list)

    await update.message.reply_text(
        f"📈 *RustChain Network*\n\n"
        f"🟢 Status: {'Online' if health.get('ok') else 'Offline'}\n"
        f"⛏ Miners: {total_miners}\n"
        f"📊 Avg antiquity multiplier: ×{avg_mult:.3f}\n"
        f"🔧 Version: {health.get('version', '?')}\n"
        f"⏱ Uptime: {health.get('uptime_s', 0)/3600:.0f}h",
        parse_mode="Markdown"
    )


# ── Main ────────────────────────────────────────────────
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: Set BOT_TOKEN environment variable!")
        print("  export BOT_TOKEN='your:botfather_token'")
        return

    app = Application.builder().token(BOT_TOKEN).rate_limiter(
        RateLimiter(max_retries=3)
    ).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("miners",  cmd_miners))
    app.add_handler(CommandHandler("epoch",   cmd_epoch))
    app.add_handler(CommandHandler("price",   cmd_price))
    app.add_handler(CommandHandler("stats",   cmd_stats))

    logger.info("RustChain Bot starting — https://t.me/RustChainBot")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
