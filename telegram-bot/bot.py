"""
RustChain Telegram Bot — @RustChainBot
Checks wallet balance, miner status, epoch info, and RTC price.

Bounty: #2869 | Reward: 10 RTC
Wallet: EVM 0x6FCBd5d14FB296933A4f5a515933B153bA24370E
"""

import asyncio
import time
from datetime import datetime
from typing import Optional

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import (
    TELEGRAM_BOT_TOKEN,
    RPC_ENDPOINTS,
    RATE_LIMIT_SECONDS,
    RTC_PRICE_USD,
)

# ── State ────────────────────────────────────────────────────────────────────
(
    AWAIT_WALLET,
) = range(1)

# Per-user rate-limit tracking: {user_id: last_timestamp}
_rate_limits: dict[int, float] = {}

# ── Helpers ──────────────────────────────────────────────────────────────────


async def fetch_json(url: str, params: dict | None = None) -> dict | None:
    """Make a GET request; return None on failure."""
    for endpoint in RPC_ENDPOINTS:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(endpoint + url, params=params or {})
                resp.raise_for_status()
                return resp.json()
        except Exception:
            continue
    return None


def rate_limited(user_id: int) -> bool:
    """Return True if the user is still in cooldown."""
    now = time.time()
    last = _rate_limits.get(user_id, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    _rate_limits[user_id] = now
    return False


def fmt_rtc(amount_str: str | float) -> str:
    """Convert raw amount string to RTC with 8 decimal places."""
    try:
        # Assume 8-decimal smallest unit
        val = float(amount_str) / 1e8
        return f"{val:.8f}".rstrip("0").rstrip(".") + " RTC"
    except Exception:
        return f"{amount_str} units"


# ── Commands ─────────────────────────────────────────────────────────────────


async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📜 Commands", callback_data="cmd_list")],
        [InlineKeyboardButton("💰 Add to Group", url="http://t.me/RustChainBot?startgroup")],
    ]
    await update.message.reply_text(
        "👋 Welcome to *RustChain Bot*!\n\n"
        "Check your RTC wallet balance, miner status, and more.\n"
        "Use /help to see all commands.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "*📖 RustChain Bot Commands*\n\n"
        "*/balance <wallet>* — Check RTC balance\n"
        "*/miners* — List active miners\n"
        "*/epoch* — Current epoch info\n"
        "*/price* — RTC reference rate\n"
        "*/help* — Show this message\n\n"
        "💡 Rate limit: 1 request / 5 seconds per user."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def balance_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if rate_limited(user_id):
        remaining = int(RATE_LIMIT_SECONDS - (time.time() - _rate_limits.get(user_id, 0)))
        await update.message.reply_text(f"⏳ Slow down! Try again in {remaining}s.")
        return

    args = ctx.args
    if not args:
        await update.message.reply_text(
            "🔹 Usage: /balance <wallet_address>\n"
            "Example: `/balance RTC1A2B3C4D5E...`",
            parse_mode="Markdown",
        )
        return

    wallet = " ".join(args).strip()
    await update.message.reply_text("⏳ Fetching balance…")

    data = await fetch_json("/wallet/balance", {"address": wallet})
    if data is None:
        await update.message.reply_text(
            "❌ Node unreachable or invalid address.\n"
            "Please try again later.",
        )
        return

    balance = data.get("balance", "N/A")
    nonce = data.get("nonce", "N/A")
    usd = float(balance) / 1e8 * RTC_PRICE_USD if balance != "N/A" else 0

    text = (
        f"*💰 Wallet Balance*\n"
        f"▸ Address: `{wallet}`\n"
        f"▸ Balance: *{fmt_rtc(balance)}*\n"
        f"▸ Nonce: `{nonce}`\n"
        f"▸ Value: ~${usd:.4f} USD"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def miners_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if rate_limited(user_id):
        remaining = int(RATE_LIMIT_SECONDS - (time.time() - _rate_limits.get(user_id, 0)))
        await update.message.reply_text(f"⏳ Slow down! Try again in {remaining}s.")
        return

    await update.message.reply_text("⏳ Fetching active miners…")

    data = await fetch_json("/miners")
    if data is None:
        await update.message.reply_text(
            "❌ Node unreachable. Could not fetch miners.",
        )
        return

    miners = data if isinstance(data, list) else data.get("miners", [])
    count = len(miners)

    lines = [f"*⛏ Active Miners — {count} total*\n"]
    for m in miners[:20]:  # cap at 20 to avoid message too long
        pub_key = m.get("public_key", "?")[:16] + "…"
        hashrate = m.get("hashrate", m.get("hash_rate", "N/A"))
        status = m.get("status", "active")
        lines.append(f"▸ `{pub_key}` | ⚡{hashrate} | {status}")

    if count > 20:
        lines.append(f"\n_…and {count - 20} more._")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def epoch_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if rate_limited(user_id):
        remaining = int(RATE_LIMIT_SECONDS - (time.time() - _rate_limits.get(user_id, 0)))
        await update.message.reply_text(f"⏳ Slow down! Try again in {remaining}s.")
        return

    await update.message.reply_text("⏳ Fetching epoch info…")

    data = await fetch_json("/epoch")
    if data is None:
        await update.message.reply_text(
            "❌ Node unreachable. Could not fetch epoch.",
        )
        return

    epoch_num = data.get("epoch_number", data.get("epoch", "?"))
    start = data.get("start_time", "?")
    end = data.get("end_time", "?")
    reward = data.get("epoch_reward", "N/A")

    # Format timestamps if they look like unix ints
    def fmt_ts(ts):
        try:
            return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            return str(ts)

    text = (
        f"*📅 Epoch #{epoch_num}*\n"
        f"▸ Start: `{fmt_ts(start)}`\n"
        f"▸ End:   `{fmt_ts(end)}`\n"
        f"▸ Reward: `{reward}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def price_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        f"*💵 RTC Reference Rate*\n\n"
        f"▸ Price: *$0.10 USD*\n"
        f"▸ Source: RustChain Foundation\n"
        f"▸ 1 RTC = $0.10\n"
        f"▸ 10 RTC = $1.00\n"
        f"▸ 100 RTC = $10.00"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def health_check(ctx: ContextTypes.DEFAULT_TYPE):
    """Periodic health check — logs node status."""
    data = await fetch_json("/health")
    if data:
        ctx.application.bot_data["node_ok"] = True
    else:
        ctx.application.bot_data["node_ok"] = False


async def unknown_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤔 Unknown command. Use /help to see available commands.",
    )


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Get one from @BotFather and set it in TELEGRAM_BOT_TOKEN env var."
        )

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("miners", miners_cmd))
    app.add_handler(CommandHandler("epoch", epoch_cmd))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))

    # Start
    print("🤖 RustChain Bot starting…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
