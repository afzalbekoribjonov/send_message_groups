"""
Bot yaratish va sozlash — barcha router'larni ro'yxatdan o'tkazadi,
middleware qo'shadi, polling boshlash funksiyasini eksport qiladi.
"""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import BOT_TOKEN

# Handler router'lari
from app.bot.handlers.start import router as start_router
from app.bot.handlers.login import router as login_router
from app.bot.handlers.broadcast import router as broadcast_router
from app.bot.handlers.groups import router as groups_router
from app.bot.handlers.stats import router as stats_router
from app.bot.handlers.help import router as help_router
from app.bot.handlers.settings import router as settings_router
from app.bot.handlers.messages import router as messages_router

# Middleware
from app.bot.middlewares import LanguageMiddleware

logger = logging.getLogger(__name__)

# ── Bot va Dispatcher yaratish ───────────────────────────────────────────────

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# FSM uchun xotira (in-memory) saqlovchi — foydalanuvchi holatlarini saqlaydi
dp = Dispatcher(storage=MemoryStorage())

# ── Middleware ro'yxatdan o'tkazish ──────────────────────────────────────────
# Message va CallbackQuery uchun til middleware'ini qo'shish
dp.message.middleware(LanguageMiddleware())
dp.callback_query.middleware(LanguageMiddleware())

# ── Router'larni ro'yxatdan o'tkazish ───────────────────────────────────────
# Stateful handler'lar FSM holati bo'yicha filtrlanadi, shuning uchun ular
# boshqa tugmalarni "yutib yubormaydi". messages_router oxirida turadi, chunki
# unda noma'lum matnlar uchun zaxira (fallback) handler joylashgan.
dp.include_routers(
    start_router,       # /start va til tanlash
    login_router,       # Akkaunt ulash (telefon, kod, 2FA)
    broadcast_router,   # Tarqatish boshlash/to'xtatish
    groups_router,      # Guruhlar boshqaruvi
    stats_router,       # Statistika
    help_router,        # Yordam
    settings_router,    # Sozlamalar (til, interval, davomiylik)
    messages_router,    # Reklama matni + zaxira handler (eng oxirida!)
)


async def start_bot() -> None:
    """Botni polling rejimida ishga tushirish.

    Bu funksiya `main.py` dan chaqiriladi.
    """
    logger.info("🤖 Xabarchi Bot ishga tushmoqda...")

    # Eski webhook'larni tozalash (agar mavjud bo'lsa)
    await bot.delete_webhook(drop_pending_updates=True)

    # Polling boshlash
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("🤖 Xabarchi Bot to'xtatildi.")
