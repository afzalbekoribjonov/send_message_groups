"""
Statistika handler'i — yuborilgan, xato, trial qoldig'i, holat.

Statistika xabari ostida inline boshqaruv tugmalari ko'rsatiladi:
tarqatishni boshlash/to'xtatish, yangilash va yopish.
"""

from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database.supabase_client import db
from app.bot.texts import get_text
from app.bot.keyboards.reply_kb import main_menu_kb
from app.bot.keyboards.inline_kb import stats_kb

logger = logging.getLogger(__name__)
router = Router(name="stats")


def _get_status_text(user: dict | None, lang: str) -> str:
    """Foydalanuvchi holatini inson tushunadigan matnga aylantirish."""
    if not user:
        return "—"

    status = user.get("status", "new")
    status_map_lat = {
        "new": "🆕 Yangi",
        "active": "✅ Faol",
        "blocked": "🚫 Bloklangan",
    }
    status_map_cyr = {
        "new": "🆕 Янги",
        "active": "✅ Фаол",
        "blocked": "🚫 Блокланган",
    }
    if lang == "uz_cyr":
        return status_map_cyr.get(status, status)
    return status_map_lat.get(status, status)


def _render_stats(telegram_id: int, lang: str) -> tuple[str, object]:
    """Statistika matni va inline klaviaturasini tayyorlaydi."""
    user = db.get_user(telegram_id)
    stats = db.get_stats(telegram_id)
    user_msg = db.get_user_message(telegram_id)

    sent_count = stats.get("sent_count", 0) if stats else 0
    failed_count = stats.get("failed_count", 0) if stats else 0
    trial_left = user.get("trial_messages_left", 0) if user else 0
    status_text = _get_status_text(user, lang)
    is_running = bool(user_msg and user_msg.get("is_running"))

    text = get_text("stats_info", lang).format(
        sent_count=sent_count,
        failed_count=failed_count,
        trial_left=trial_left,
        status=status_text,
    )
    if is_running:
        text += "\n\n" + get_text("broadcast_state_running", lang)
    else:
        text += "\n\n" + get_text("broadcast_state_stopped", lang)

    return text, stats_kb(lang, is_running)


@router.message(F.text.in_({"📊 Statistika", "📊 Статистика"}))
async def show_stats(
    message: Message, state: FSMContext, lang: str = "uz_lat", is_linked: bool = False
) -> None:
    """Foydalanuvchi statistikasini ko'rsatish."""
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

    try:
        text, kb = _render_stats(telegram_id, lang)
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error("Statistika olishda xato: %s", e)
        await message.answer(
            get_text("error_generic", lang),
            reply_markup=main_menu_kb(lang, is_linked),
            parse_mode="HTML",
        )


# ── Inline tugmalar (callback) ───────────────────────────────────────────────

async def _refresh_message(callback: CallbackQuery, lang: str) -> None:
    """Statistika xabarini yangilash (o'zgarmagan bo'lsa xatoni e'tiborsiz qoldiradi)."""
    telegram_id = callback.from_user.id
    text, kb = _render_stats(telegram_id, lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest:
        pass  # "message is not modified" — e'tiborsiz


@router.callback_query(F.data == "stats_refresh")
async def cb_refresh(callback: CallbackQuery, lang: str = "uz_lat") -> None:
    """Statistikani yangilash."""
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    await _refresh_message(callback, lang)
    await callback.answer(get_text("stats_refreshed", lang))


@router.callback_query(F.data == "stats_close")
async def cb_close(callback: CallbackQuery, lang: str = "uz_lat") -> None:
    """Statistika xabarini yopish (o'chirish)."""
    if not callback.message:
        await callback.answer()
        return
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(F.data == "bc_stop")
async def cb_stop(callback: CallbackQuery, lang: str = "uz_lat") -> None:
    """Tarqatishni to'xtatish."""
    if not callback.from_user or not callback.message:
        await callback.answer()
        return

    telegram_id = callback.from_user.id
    try:
        db.set_message_running(telegram_id, False)
        await _refresh_message(callback, lang)
        await callback.answer(get_text("broadcast_stopped", lang), show_alert=True)
    except Exception as e:
        logger.error("Callback stop xatosi: %s", e)
        await callback.answer(get_text("error_generic", lang), show_alert=True)


@router.callback_query(F.data == "bc_start")
async def cb_start(callback: CallbackQuery, lang: str = "uz_lat") -> None:
    """Tarqatishni boshlash (tekshiruvlar bilan)."""
    if not callback.from_user or not callback.message:
        await callback.answer()
        return

    telegram_id = callback.from_user.id
    try:
        # 1. Reklama matni
        user_msg = db.get_user_message(telegram_id)
        if not user_msg or not user_msg.get("message_text"):
            await callback.answer(get_text("no_message_set", lang), show_alert=True)
            return
        # 2. Faol guruhlar
        if not db.get_active_groups(telegram_id):
            await callback.answer(get_text("no_groups_selected", lang), show_alert=True)
            return
        # 3. Yuborish huquqi (trial/obuna)
        can_send, reason = db.can_send_message(telegram_id)
        if not can_send:
            if reason == "trial_expired":
                await callback.answer(get_text("trial_expired_short", lang), show_alert=True)
            else:
                await callback.answer(get_text("error_generic", lang), show_alert=True)
            return

        db.set_message_running(telegram_id, True)
        await _refresh_message(callback, lang)
        await callback.answer(get_text("broadcast_started", lang), show_alert=True)
    except Exception as e:
        logger.error("Callback start xatosi: %s", e)
        await callback.answer(get_text("error_generic", lang), show_alert=True)
