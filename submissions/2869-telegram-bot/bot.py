"""
RustChain Telegram Bot — Bounty #2869
@RustChainBot - Wallet balance and miner status checker

Commands:
  /balance <miner_id> - Check RTC wallet balance
  /miners            - List active miners
  /epoch             - Current epoch info
  /price             - Show RTC reference rate
  /help              - Show help

Deploy: Railway / Fly.io / systemd (see README.md)
"""

import os
import re
import time
import logging
from functools import wraps
from typing import Optional

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ── Configuration ─────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
NODE_URL = os.environ.get("RUSTCHAIN_NODE_URL", "https://50.28.86.131").rstrip("/")
RATE_LIMIT_SECONDS = 5

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Rate Limiter ───────────────────────────────────────────────────────────────
# In-memory store: {user_id: last_request_timestamp}
_user_rate_limit: dict[int, float] = {}


def rate_limit(seconds: int = RATE_LIMIT_SECONDS):
    """Decorator: enforces per-user rate limiting."""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            now = time.time()
            last = _user_rate_limit.get(user_id, 0)
            if now - last < seconds:
                remaining = round(seconds - (now - last), 1)
                await update.message.reply_text(
                    f"⏳ Rate limit: please wait {remaining}s before next command."
                )
                return
            _user_rate_limit[user_id] = now
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


# ── Node API helpers ───────────────────────────────────────────────────────────
def get_json(endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
    """Fetch JSON from the RustChain node API with error handling."""
    url = f"{NODE_URL}{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.warning("API error %s %s: %s", url, params, e)
        return None


def format_balance(data: dict) -> str:
    """Format wallet balance response."""
    amount = data.get("amount_rtc") or data.get("amount", data.get("balance", 0))
    return f"💰 **Balance:** `{amount}` RTC"


# ── Commands ──────────────────────────────────────────────────────────────────
@rate_limit()
async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check RTC wallet balance for a given miner_id."""
    if not context.args:
        await update.message.reply_text(
            "📖 Usage: `/balance <miner_id>`\n"
            "Example: `/balance alice_miner`",
            parse_mode="Markdown",
        )
        return

    miner_id = context.args[0].strip()
    data = get_json("/wallet/balance", {"miner_id": miner_id})

    if data is None or data.get("error"):
        err = data.get("error", "Unable to reach node") if data else "No response"
        await update.message.reply_text(f"❌ Error: `{err}`", parse_mode="Markdown")
        return

    amount = data.get("amount_rtc") or data.get("amount", 0)
    await update.message.reply_text(
        f"💰 **Wallet Balance**\n\n"
        f"🆔 Miner ID: `{miner_id}`\n"
        f"💵 Balance: `{amount}` RTC\n"
        f"✅ Node: healthy",
        parse_mode="Markdown",
    )


@rate_limit()
async def cmd_miners(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List active miners."""
    data = get_json("/api/miners")

    if data is None:
        await update.message.reply_text("❌ Unable to fetch miners list.")
        return

    miners: list = data if isinstance(data, list) else data.get("miners", [])

    if not miners:
        await update.message.reply_text("🔍 No active miners found.")
        return

    # Show top 10 miners by antiquity (first 10 in list)
    lines = ["⛏️ **Active Miners**\n"]
    for i, m in enumerate(miners[:10], 1):
        name = m.get("miner_id") or m.get("name") or m.get("address", "?")
        status = m.get("status", "active")
        lines.append(f"  {i}. `{name}` — {status}")

    total = len(miners)
    if total > 10:
        lines.append(f"\n_...and {total - 10} more miners._")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@rate_limit()
async def cmd_epoch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current epoch info."""
    data = get_json("/epoch")

    if data is None:
        await update.message.reply_text("❌ Unable to fetch epoch info.")
        return

    epoch = data.get("epoch", "?")
    block = data.get("block", data.get("height", "?"))
    validators = data.get("validators", "?")
    status = data.get("status", "synced")

    await update.message.reply_text(
        f"📅 **Epoch Info**\n\n"
        f"🔢 Epoch: `{epoch}`\n"
        f"🧱 Block: `{block}`\n"
        f"👥 Validators: `{validators}`\n"
        f"📡 Node Status: `{status}`",
        parse_mode="Markdown",
    )


@rate_limit()
async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show RTC reference price."""
    price_usd = 0.10  # Fixed reference rate per bounty spec
    await update.message.reply_text(
        f"💲 **RTC Reference Rate**\n\n"
        f"📌 1 RTC = **$0.10 USD**\n"
        f"_(Fixed reference rate as per RustChain policy)_",
        parse_mode="Markdown",
    )


@rate_limit()
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quick network overview combining multiple endpoints."""
    # Fetch health + epoch in parallel would be ideal, but sequential is fine
    health = get_json("/health")
    epoch_data = get_json("/epoch")

    parts = ["📊 **RustChain Network Overview**\n"]

    if health:
        parts.append(f"✅ Node: healthy")
        parts.append(f"⏱️ Uptime: {health.get('uptime', '?')}")
    else:
        parts.append("❌ Node: unreachable")

    if epoch_data:
        parts.append(f"🔢 Epoch: {epoch_data.get('epoch', '?')}")
        parts.append(f"🧱 Block: {epoch_data.get('block', '?')}")

    keyboard = [
        [InlineKeyboardButton("💰 Check Balance", callback_data="cb_balance")],
        [InlineKeyboardButton("⛏️ Active Miners", callback_data="cb_miners")],
        [InlineKeyboardButton("📅 Epoch Info", callback_data="cb_epoch")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "\n".join(parts),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help / command list."""
    await update.message.reply_text(
        "🤖 **RustChain Bot Commands**\n\n"
        " `/balance <miner_id>` — Check wallet balance\n"
        " `/miners`            — List active miners\n"
        " `/epoch`             — Current epoch info\n"
        " `/price`             — RTC reference rate\n"
        " `/stats`             — Network overview\n"
        " `/help`              — Show this message\n\n"
        "_Rate limit: 1 request per 5 seconds per user_",
        parse_mode="Markdown",
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message."""
    await update.message.reply_text(
        "👋 Welcome to the RustChain Telegram Bot!\n\n"
        "Use /help to see available commands.",
        parse_mode="Markdown",
    )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands gracefully."""
    await update.message.reply_text(
        "❓ Unknown command. Use /help for available commands.",
        parse_mode="Markdown",
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required.")

    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("miners", cmd_miners))
    app.add_handler(CommandHandler("epoch", cmd_epoch))
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("🤖 RustChain Telegram Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
