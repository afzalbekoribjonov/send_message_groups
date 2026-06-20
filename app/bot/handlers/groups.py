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
from app.bot.keyboards.inline_kb import groups_kb

logger = logging.getLogger(__name__)
router = Router(name="groups")


@router.message(F.text.in_({"📋 Guruhlar", "📋 Гуруҳлар"}))
async def show_groups(
    message: Message, state: FSMContext, lang: str = "uz_lat", is_linked: bool = False
) -> None:
    """Guruhlar tugmasi bosilganda — Pyrogram orqali guruhlarni yuklash
    va inline toggle ko'rsatish."""
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

        # DB'dan yangilangan guruhlar ro'yxatini olish
        db_groups = db.get_user_groups(telegram_id)

        await loading_msg.edit_text(
            get_text("groups_list", lang),
            reply_markup=groups_kb(db_groups, lang),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error("Guruhlarni yuklashda xato (telegram_id=%d): %s", telegram_id, e)
        await loading_msg.edit_text(
            get_text("error_generic", lang),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("toggle_group_"))
async def toggle_group_callback(callback: CallbackQuery, lang: str = "uz_lat") -> None:
    """Guruhni yoqish/o'chirish toggle."""
    if not callback.from_user or not callback.message:
        await callback.answer()
        return

    telegram_id = callback.from_user.id
    group_id = callback.data.replace("toggle_group_", "")

    try:
        # Hozirgi guruhlar ro'yxati
        all_groups = db.get_user_groups(telegram_id)
        target_group = None

        for g in all_groups:
            if str(g.get("id")) == group_id:
                target_group = g
                break

        if not target_group:
            await callback.answer("⚠️ Guruh topilmadi!", show_alert=True)
            return

        current_active = target_group.get("is_active", False)
        new_active = not current_active

        # Agar yoqmoqchi bo'lsa — maksimal son tekshiruvi
        if new_active:
            active_count = sum(1 for g in all_groups if g.get("is_active"))
            if active_count >= MAX_GROUPS_PER_USER:
                await callback.answer(
                    get_text("max_groups_reached", lang).format(max=MAX_GROUPS_PER_USER),
                    show_alert=True,
                )
                return

        # Toggle
        db.toggle_group(group_id, new_active)

        title = target_group.get("group_title", "Nomsiz")
        if new_active:
            await callback.answer(
                get_text("group_selected", lang).format(title=title),
            )
        else:
            await callback.answer(
                get_text("group_deselected", lang).format(title=title),
            )

        # Klaviaturani yangilash
        updated_groups = db.get_user_groups(telegram_id)
        await callback.message.edit_reply_markup(
            reply_markup=groups_kb(updated_groups, lang),
        )

    except Exception as e:
        logger.error("Guruh toggle xatosi: %s", e)
        await callback.answer(
            get_text("error_generic", lang),
            show_alert=True,
        )
