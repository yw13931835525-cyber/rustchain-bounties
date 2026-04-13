"""
Configuration for RustChain Telegram Bot.
Load from environment variables or .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── RustChain RPC ───────────────────────────────────────────────────────────
# Public node endpoints (bot will try in order)
RPC_ENDPOINTS = [
    os.getenv("RPC_URL", "https://50.28.86.131"),
]

# ── Rate Limiting ───────────────────────────────────────────────────────────
# Minimum seconds between commands per user
RATE_LIMIT_SECONDS = 5

# ── RTC Reference Price ─────────────────────────────────────────────────────
RTC_PRICE_USD = 0.10
