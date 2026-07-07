"""
Guruhlar boshqaruvi handler'i.
Pyrogram orqali foydalanuvchining guruhlarini yuklaydi,
DB bilan sinxronlashtiradi, toggle inline klaviatura ko'rsatadi.
"""

from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from pyrogram import Client
from pyrogram.enums import ChatType

from app.config import API_ID, API_HASH, MAX_GROUPS_PER_USER
from app.database.supabase_client import db
from app.bot.texts import get_text
from app.bot.keyboards.reply_kb import main_menu_kb
from app.bot.keyboards.inline_kb import groups_webapp_kb

logger = logging.getLogger(__name__)
router = Router(name="groups")


@router.message(F.text.in_({"📋 Guruhlar", "📋 Гуруҳлар"}))
async def show_groups(
    message: Message, state: FSMContext, lang: str = "uz_lat", is_linked: bool = False
) -> None:
    """Guruhlar tugmasi bosilganda — Pyrogram orqali guruhlarni yuklash
    va WebApp tugmasini ko'rsatish."""
    if not message.from_user:
        return

    await state.clear()
    telegram_id = message.from_user.id

    if not is_linked:
        await message.answer(
            get_text("no_account", lang),
            reply_markup=main_menu_kb(lang, is_linked),
            parse_mode="HTML",
        )
        return

    # Session string tekshiruvi
    try:
        session_string = db.get_session_string(telegram_id)
    except Exception as e:
        logger.error("Session olishda xato: %s", e)
        await message.answer(get_text("error_generic", lang), parse_mode="HTML")
        return

    if not session_string:
        await message.answer(
            get_text("no_account", lang),
            reply_markup=main_menu_kb(lang),
            parse_mode="HTML",
        )
        return

    # Yuklanmoqda xabari
    loading_msg = await message.answer(
        get_text("groups_loading", lang),
        parse_mode="HTML",
    )

    # Pyrogram orqali guruhlarni yuklash
    try:
        client = Client(
            name=f"groups_{telegram_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True,
        )

        groups_from_tg: list[dict] = []

        async with client:
            async for dialog in client.get_dialogs():
                chat = dialog.chat
                if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
                    groups_from_tg.append({
                        "chat_id": chat.id,
                        "title": chat.title or "Nomsiz guruh",
                    })

        if not groups_from_tg:
            await loading_msg.edit_text(
                get_text("no_groups", lang),
                parse_mode="HTML",
            )
            return

        # DB bilan sinxronlashtirish
        db.sync_user_groups(telegram_id, groups_from_tg)

        # WebApp tugmasini yuborish
        await loading_msg.edit_text(
            "Guruhlarni boshqarish uchun quyidagi tugmani bosing:",
            reply_markup=groups_webapp_kb(lang),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error("Guruhlarni yuklashda xato (telegram_id=%d): %s", telegram_id, e)
        await loading_msg.edit_text(
            get_text("error_generic", lang),
            parse_mode="HTML",
        )
