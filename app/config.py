"""
Loyiha konfiguratsiyasi.
Barcha sozlamalar .env faylidan yuklanadi.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylini yuklash
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ── Telegram Bot (aiogram) ──────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── Telegram API (Pyrogram Userbot) ─────────────────────────────────────────
API_ID: int = int(os.getenv("API_ID", "0"))
API_HASH: str = os.getenv("API_HASH", "")

# ── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# ── Admin Panel ──────────────────────────────────────────────────────────────
ADMIN_SECRET_KEY: str = os.getenv("ADMIN_SECRET_KEY", "change-me-please-32chars-minimum")
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")

# ── Server ───────────────────────────────────────────────────────────────────
PORT: int = int(os.getenv("PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://your-domain.com/webapp/groups")

# ── Xabar yuborish cheklovlari ──────────────────────────────────────────────
MIN_INTERVAL_MINUTES: int = 2          # Minimal xabar yuborish oralig'i (daqiqa)
MAX_GROUPS_PER_USER: int = 15          # Bitta foydalanuvchi uchun max guruhlar soni
FREE_TRIAL_MESSAGES: int = 15          # Bepul sinov xabarlari soni
JITTER_MIN_SECONDS: int = 5            # Random kechikish (min)
JITTER_MAX_SECONDS: int = 15           # Random kechikish (max)

# ── Yordam ma'lumotlari ─────────────────────────────────────────────────────
SUPPORT_USERNAME: str = "@uzafo"
SUPPORT_PHONE: str = "+998 94 108 09 16"
