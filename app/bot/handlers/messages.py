"""
Reklama matni boshqaruvi handler'i.
Foydalanuvchi reklama matnini ko'rishi, yangi matn kiritishi mumkin.

Shuningdek bu yerda umumiy «⬅️ Ortga» tugmasi va noma'lum matnlar uchun
zaxira (fallback) handler joylashgan — shu sababli bu router eng oxirida
ro'yxatdan o'tkaziladi.
"""

from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database.supabase_client import db
from app.bot.texts import get_text
from app.bot.states import AdStates
from app.bot.keyboards.reply_kb import main_menu_kb, back_kb, language_kb

logger = logging.getLogger(__name__)
router = Router(name="messages")


@router.message(F.text.in_({"📝 Reklama matni", "📝 Реклама матни"}))
async def show_ad_text(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
) -> None:
    """Reklama matni tugmasi bosilganda — hozirgi matnni ko'rsatish
    yoki yangi matn kiritishni so'rash."""
    if not message.from_user:
        return

    telegram_id = message.from_user.id

    if not is_linked:
        await message.answer(
            get_text("no_account", lang),
            reply_markup=main_menu_kb(lang, is_linked),
            parse_mode="HTML",
        )
        return

    try:
        user_msg = db.get_user_message(telegram_id)
    except Exception as e:
        logger.error("Reklama matnini olishda xato: %s", e)
        await message.answer(get_text("error_generic", lang), parse_mode="HTML")
        return

    if user_msg and user_msg.get("message_text"):
        text = get_text("current_ad", lang).format(text=user_msg["message_text"])
    else:
        text = get_text("no_ad_text", lang)

    await state.set_state(AdStates.waiting_text)
    await message.answer(text, reply_markup=back_kb(lang), parse_mode="HTML")


@router.message(F.text.in_({"⬅️ Ortga", "⬅️ Ортга"}))
async def back_to_menu(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
    is_running: bool = False,
) -> None:
    """«Ortga» tugmasi — har qanday holatni tozalab, asosiy menyuga qaytaradi."""
    if not message.from_user:
        return

    await state.clear()
    await message.answer(
        get_text("main_menu", lang),
        reply_markup=main_menu_kb(lang, is_linked, is_running),
        parse_mode="HTML",
    )


@router.message(AdStates.waiting_text, F.text)
async def receive_ad_text(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
) -> None:
    """Yangi reklama matnini qabul qilish (faqat AdStates.waiting_text holatida)."""
    if not message.from_user:
        return

    telegram_id = message.from_user.id
    ad_text = (message.html_text or "").strip()
    if not ad_text:
        await message.answer(get_text("no_ad_text", lang), parse_mode="HTML")
        return

    try:
        db.set_user_message(telegram_id, ad_text)
        await state.clear()
        await message.answer(
            get_text("ad_text_saved", lang),
            reply_markup=main_menu_kb(lang, is_linked),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Reklama matnini saqlashda xato: %s", e)
        await message.answer(get_text("error_generic", lang), parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════════════════
# ZAXIRA (FALLBACK) — hech qaysi handler tutmagan matnlar
# Bu handler eng oxirgi router'ning eng oxirida turishi shart.
# ═══════════════════════════════════════════════════════════════════════════

@router.message(F.text)
async def fallback_handler(
    message: Message,
    lang: str = "uz_lat",
    is_linked: bool = False,
    is_running: bool = False,
) -> None:
    """Noma'lum matn — foydalanuvchini menyuga yo'naltiradi.

    Agar foydalanuvchi hali tilni tanlamagan bo'lsa, til tanlash so'raladi.
    """
    if not message.from_user:
        return

    # Til hali tanlanmaganmi?
    try:
        user = db.get_user(message.from_user.id)
        if not user or not user.get("language"):
            await message.answer(
                get_text("welcome", lang),
                reply_markup=language_kb(),
                parse_mode="HTML",
            )
            return
    except Exception:
        pass

    await message.answer(
        get_text("main_menu", lang),
        reply_markup=main_menu_kb(lang, is_linked, is_running),
        parse_mode="HTML",
    )
