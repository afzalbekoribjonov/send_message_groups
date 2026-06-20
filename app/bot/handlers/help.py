"""
Yordam handler'i — foydalanuvchiga bot haqida ma'lumot va aloqa beradi.
"""

from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import SUPPORT_PHONE, SUPPORT_USERNAME, FREE_TRIAL_MESSAGES
from app.bot.texts import get_text
from app.bot.keyboards.reply_kb import main_menu_kb

logger = logging.getLogger(__name__)
router = Router(name="help")


@router.message(F.text.in_({"ℹ️ Yordam", "ℹ️ Ёрдам"}))
async def show_help(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
    is_running: bool = False,
) -> None:
    """Yordam matnini ko'rsatish — bot haqida qo'llanma + aloqa."""
    if not message.from_user:
        return

    await state.clear()
    text = get_text("help_text", lang).format(
        trial=FREE_TRIAL_MESSAGES,
        support_phone=SUPPORT_PHONE,
        support_username=SUPPORT_USERNAME,
    )

    await message.answer(
        text,
        reply_markup=main_menu_kb(lang, is_linked, is_running),
        parse_mode="HTML",
    )
