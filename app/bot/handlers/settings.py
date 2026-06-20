"""
Sozlamalar handler'i — til, interval, davomiylik, hisobdan chiqish.

Til o'zgartirish tugmalari (Lotin/Kirill) start.py da global tutiladi, shu
sababli bu yerda takrorlanmaydi — sozlamalardan tilni almashtirish ham o'sha
handler orqali ishlaydi.
"""

from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.config import MIN_INTERVAL_MINUTES
from app.database.supabase_client import db
from app.bot.texts import get_text
from app.bot.states import SettingsStates
from app.bot.keyboards.reply_kb import main_menu_kb, settings_kb
from app.bot.keyboards.inline_kb import confirm_logout_kb

logger = logging.getLogger(__name__)
router = Router(name="settings")


@router.message(F.text.in_({"⚙️ Sozlamalar", "⚙️ Созламалар"}))
async def show_settings(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
) -> None:
    """Sozlamalar menyusini ko'rsatish."""
    if not message.from_user:
        return

    await state.clear()
    await message.answer(
        get_text("settings_title", lang),
        reply_markup=settings_kb(lang, is_linked),
        parse_mode="HTML",
    )


@router.message(F.text.in_({"⏱ Interval", "⏱ Интервал"}))
async def ask_interval(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
) -> None:
    """Interval o'zgartirish — hozirgi qiymatni ko'rsatish va yangi son so'rash."""
    if not message.from_user:
        return

    if not is_linked:
        await message.answer(
            get_text("no_account", lang),
            reply_markup=main_menu_kb(lang, is_linked),
            parse_mode="HTML",
        )
        return

    telegram_id = message.from_user.id
    try:
        user_msg = db.get_user_message(telegram_id)
        current_interval = user_msg.get("interval_minutes", MIN_INTERVAL_MINUTES) if user_msg else MIN_INTERVAL_MINUTES
    except Exception:
        current_interval = MIN_INTERVAL_MINUTES

    await state.set_state(SettingsStates.waiting_interval)
    await message.answer(
        get_text("settings_interval", lang).format(interval=current_interval),
        parse_mode="HTML",
    )


@router.message(F.text.in_({"⏳ Davomiylik", "⏳ Давомийлик"}))
async def ask_duration(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
) -> None:
    """Davomiylik o'zgartirish — hozirgi qiymatni ko'rsatish va yangi son so'rash."""
    if not message.from_user:
        return

    if not is_linked:
        await message.answer(
            get_text("no_account", lang),
            reply_markup=main_menu_kb(lang, is_linked),
            parse_mode="HTML",
        )
        return

    telegram_id = message.from_user.id
    try:
        user_msg = db.get_user_message(telegram_id)
        current_duration = user_msg.get("duration_hours", 0) if user_msg else 0
    except Exception:
        current_duration = 0

    await state.set_state(SettingsStates.waiting_duration)
    await message.answer(
        get_text("settings_duration", lang).format(duration=current_duration),
        parse_mode="HTML",
    )


# ── Son kiritish (interval) ──────────────────────────────────────────────────

@router.message(SettingsStates.waiting_interval, F.text)
async def receive_interval(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
) -> None:
    """Interval qiymatini qabul qilish (daqiqa)."""
    if not message.from_user:
        return

    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(get_text("enter_number", lang), parse_mode="HTML")
        return

    value = int(raw)
    if value < MIN_INTERVAL_MINUTES:
        await message.answer(get_text("interval_too_low", lang), parse_mode="HTML")
        return

    telegram_id = message.from_user.id
    try:
        db.upsert_message_settings(telegram_id, interval_minutes=value)
        await state.clear()
        await message.answer(
            get_text("interval_set", lang).format(interval=value),
            reply_markup=settings_kb(lang, is_linked),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Interval saqlashda xato: %s", e)
        await message.answer(get_text("error_generic", lang), parse_mode="HTML")


# ── Son kiritish (davomiylik) ────────────────────────────────────────────────

@router.message(SettingsStates.waiting_duration, F.text)
async def receive_duration(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
) -> None:
    """Davomiylik qiymatini qabul qilish (soat, 0 = cheksiz)."""
    if not message.from_user:
        return

    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(get_text("enter_number", lang), parse_mode="HTML")
        return

    value = int(raw)
    telegram_id = message.from_user.id
    try:
        db.upsert_message_settings(telegram_id, duration_hours=value)
        await state.clear()
        await message.answer(
            get_text("duration_set", lang).format(duration=value),
            reply_markup=settings_kb(lang, is_linked),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Davomiylik saqlashda xato: %s", e)
        await message.answer(get_text("error_generic", lang), parse_mode="HTML")


# ── Hisobdan chiqish ─────────────────────────────────────────────────────────

@router.message(F.text.in_({"🚪 Hisobdan chiqish", "🚪 Ҳисобдан чиқиш"}))
async def logout_handler(
    message: Message,
    state: FSMContext,
    lang: str = "uz_lat",
    is_linked: bool = False,
    is_running: bool = False,
) -> None:
    """Hisobdan chiqish — avval inline tasdiqlash so'raladi."""
    if not message.from_user:
        return

    if not is_linked:
        await message.answer(
            get_text("no_account", lang),
            reply_markup=main_menu_kb(lang, is_linked, is_running),
            parse_mode="HTML",
        )
        return

    await message.answer(
        get_text("logout_confirm", lang),
        reply_markup=confirm_logout_kb(lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "logout_yes")
async def logout_confirm_yes(
    callback: CallbackQuery, state: FSMContext, lang: str = "uz_lat"
) -> None:
    """Hisobdan chiqishni tasdiqlash — sessiyani o'chiradi."""
    if not callback.from_user or not callback.message:
        await callback.answer()
        return

    await state.clear()
    telegram_id = callback.from_user.id
    try:
        db.set_message_running(telegram_id, False)
        db.update_user(telegram_id, session_string=None, status="new")
        logger.info("Foydalanuvchi tizimdan chiqdi: %d", telegram_id)
        await callback.message.edit_text(
            get_text("logout_success", lang),
            parse_mode="HTML",
        )
        await callback.message.answer(
            get_text("main_menu", lang),
            reply_markup=main_menu_kb(lang, is_linked=False),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Tizimdan chiqishda xato: %s", e)
        await callback.message.answer(
            get_text("error_generic", lang),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "logout_no")
async def logout_confirm_no(callback: CallbackQuery, lang: str = "uz_lat") -> None:
    """Hisobdan chiqish bekor qilindi."""
    if not callback.message:
        await callback.answer()
        return
    await callback.message.edit_text(
        get_text("logout_cancelled", lang),
        parse_mode="HTML",
    )
    await callback.answer()
