"""
Tarqatish (Broadcast) boshqaruvi — boshlash va to'xtatish.
Xabar + guruhlar mavjudligini tekshiradi, is_running holatini boshqaradi.
"""

from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database.supabase_client import db
from app.bot.texts import get_text
from app.bot.keyboards.reply_kb import main_menu_kb

logger = logging.getLogger(__name__)
router = Router(name="broadcast")


@router.message(F.text.in_({
    "🚀 Tarqatishni boshlash", "🚀 Тарқатишни бошлаш",
}))
async def start_broadcast(
    message: Message, state: FSMContext, lang: str = "uz_lat", is_linked: bool = False
) -> None:
    """Xabar tarqatishni boshlash.

    Tekshiruvlar:
    1. Akkaunt ulangan bo'lishi kerak (session_string)
    2. Reklama matni kiritilgan bo'lishi kerak
    3. Kamida bitta faol guruh tanlangan bo'lishi kerak
    4. Foydalanuvchi xabar yuborish huquqiga ega bo'lishi kerak (trial/obuna)
    5. Hozirda ishlamayotgan bo'lishi kerak
    """
    if not message.from_user:
        return

    await state.clear()
    telegram_id = message.from_user.id

    try:
        # 1. Akkaunt tekshiruvi
        session_string = db.get_session_string(telegram_id)
        if not session_string or not is_linked:
            await message.answer(
                get_text("no_account", lang),
                reply_markup=main_menu_kb(lang, is_linked=False),
                parse_mode="HTML",
            )
            return

        # 2. Reklama matni tekshiruvi
        user_msg = db.get_user_message(telegram_id)
        if not user_msg or not user_msg.get("message_text"):
            await message.answer(
                get_text("no_message_set", lang),
                reply_markup=main_menu_kb(lang, is_linked),
                parse_mode="HTML",
            )
            return

        # 3. Allaqachon ishlayotganligini tekshirish
        if user_msg.get("is_running"):
            await message.answer(
                get_text("broadcast_already_running", lang),
                reply_markup=main_menu_kb(lang, is_linked, is_running=True),
                parse_mode="HTML",
            )
            return

        # 4. Faol guruhlar tekshiruvi
        active_groups = db.get_active_groups(telegram_id)
        if not active_groups:
            await message.answer(
                get_text("no_groups_selected", lang),
                reply_markup=main_menu_kb(lang, is_linked),
                parse_mode="HTML",
            )
            return

        # 5. Yuborish huquqi tekshiruvi (trial/obuna)
        can_send, reason = db.can_send_message(telegram_id)
        if not can_send:
            if reason == "trial_expired":
                from app.config import SUPPORT_PHONE, SUPPORT_USERNAME
                await message.answer(
                    get_text("trial_expired", lang).format(
                        support_phone=SUPPORT_PHONE,
                        support_username=SUPPORT_USERNAME,
                    ),
                    reply_markup=main_menu_kb(lang, is_linked),
                    parse_mode="HTML",
                )
            else:
                await message.answer(
                    get_text("error_generic", lang),
                    reply_markup=main_menu_kb(lang, is_linked),
                    parse_mode="HTML",
                )
            return

        # ✅ Barcha tekshiruvlar o'tdi — tarqatishni boshlash
        db.set_message_running(telegram_id, True)

        await message.answer(
            get_text("broadcast_started", lang),
            reply_markup=main_menu_kb(lang, is_linked, is_running=True),
            parse_mode="HTML",
        )
        logger.info("Tarqatish boshlandi: telegram_id=%d", telegram_id)

    except Exception as e:
        logger.error("Tarqatish boshlashda xato: %s", e)
        await message.answer(
            get_text("error_generic", lang),
            reply_markup=main_menu_kb(lang, is_linked),
            parse_mode="HTML",
        )


@router.message(F.text.in_({
    "🛑 Tarqatishni to'xtatish", "🛑 Тарқатишни тўхтатиш",
}))
async def stop_broadcast(
    message: Message, state: FSMContext, lang: str = "uz_lat", is_linked: bool = False
) -> None:
    """Xabar tarqatishni to'xtatish."""
    if not message.from_user:
        return

    await state.clear()
    telegram_id = message.from_user.id

    try:
        user_msg = db.get_user_message(telegram_id)

        if not user_msg or not user_msg.get("is_running"):
            await message.answer(
                get_text("broadcast_not_running", lang),
                reply_markup=main_menu_kb(lang, is_linked),
                parse_mode="HTML",
            )
            return

        db.set_message_running(telegram_id, False)

        await message.answer(
            get_text("broadcast_stopped", lang),
            reply_markup=main_menu_kb(lang, is_linked),
            parse_mode="HTML",
        )
        logger.info("Tarqatish to'xtatildi: telegram_id=%d", telegram_id)

    except Exception as e:
        logger.error("Tarqatish to'xtatishda xato: %s", e)
        await message.answer(
            get_text("error_generic", lang),
            reply_markup=main_menu_kb(lang, is_linked),
            parse_mode="HTML",
        )
