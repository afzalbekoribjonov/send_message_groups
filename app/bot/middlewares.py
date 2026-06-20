"""
Aiogram middleware'lari.
LanguageMiddleware — har bir handler'ga foydalanuvchi tilini qo'shadi.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.database.supabase_client import db

logger = logging.getLogger(__name__)


class LanguageMiddleware(BaseMiddleware):
    """Har bir so'rovda foydalanuvchi tilini DB'dan yuklaydi
    va handler ma'lumotlariga 'lang' kalitini qo'shadi.

    Agar foydalanuvchi DB'da topilmasa, standart til 'uz_lat' ishlatiladi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Telegram ID ni aniqlash
        telegram_id: int | None = None

        if isinstance(event, Message) and event.from_user:
            telegram_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            telegram_id = event.from_user.id

        # Standart til va holat
        lang = "uz_lat"
        is_linked = False
        is_running = False
        user = None

        if telegram_id:
            try:
                user = db.get_user(telegram_id)
                if user:
                    # language NULL bo'lishi mumkin (til hali tanlanmagan) —
                    # bunday holatda standart tilga tushamiz.
                    lang = user.get("language") or "uz_lat"
                    is_linked = bool(user.get("session_string"))
                # Tarqatish holati — faqat ulangan foydalanuvchi va matnli xabar
                # uchun (asosiy menyu klaviaturasini to'g'ri ko'rsatish maqsadida).
                if is_linked and isinstance(event, Message):
                    user_msg = db.get_user_message(telegram_id)
                    is_running = bool(user_msg and user_msg.get("is_running"))
            except Exception as e:
                logger.warning("LanguageMiddleware — ma'lumot yuklashda xato: %s", e)

        # Handler ma'lumotlariga qo'shish.
        # user — middleware allaqachon o'qigan ma'lumot; handler'lar uni qayta
        # so'ramasligi uchun uzatamiz (ortiqcha DB so'rovini kamaytiradi).
        data["user"] = user
        data["lang"] = lang
        data["is_linked"] = is_linked
        data["is_running"] = is_running
        return await handler(event, data)
