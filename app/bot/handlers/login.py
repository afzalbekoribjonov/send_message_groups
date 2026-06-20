"""
Akkauntni ulash (Login) handler — ENG MUHIM handler.

Flow:
1. Foydalanuvchi «🔗 Akkauntni ulash» tugmasini bosadi.
2. Bot telefon raqamni so'raydi.
3. Bot Pyrogram orqali kod yuboradi.
4. Bot inline numpad klaviatura ko'rsatadi.
5. Foydalanuvchi kodni raqam-raqam kiritadi (yulduzchalar sifatida ko'rinadi).
6. Tasdiqlashda Pyrogram sign_in qiladi.
7. Agar 2FA kerak bo'lsa, parolni matn sifatida so'raydi.
8. session_string DB'ga saqlanadi.

Holatlar FSM (LoginStates) orqali boshqariladi. Live Pyrogram Client va
oraliq ma'lumotlar FSM data'sida (xotirada) saqlanadi — shu sababli login
oqimidagi handler'lar boshqa tugmalarni "yutib yubormaydi".
"""

from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from pyrogram import Client
from pyrogram.enums import SentCodeType
from pyrogram.errors import (
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    BadRequest,
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneNumberBanned,
    PhoneNumberFlood,
    FloodWait,
)

from app.config import API_ID, API_HASH
from app.database.supabase_client import db
from app.bot.texts import get_text
from app.bot.states import LoginStates
from app.bot.keyboards.reply_kb import main_menu_kb, back_kb
from app.bot.keyboards.inline_kb import code_input_kb

logger = logging.getLogger(__name__)
router = Router(name="login")

CODE_LENGTH = 5


def _format_entered(entered: str, total: int = CODE_LENGTH) -> str:
    """Kiritilgan raqamlarni yulduzcha va bo'sh joy bilan formatlaydi.

    Misol: entered='12', total=5 => '* * _ _ _'
    """
    return " ".join("*" if i < len(entered) else "_" for i in range(total))


_CODE_TYPE_KEYS = {
    SentCodeType.APP: "code_via_app",
    SentCodeType.SMS: "code_via_sms",
    SentCodeType.CALL: "code_via_call",
    SentCodeType.FLASH_CALL: "code_via_flash_call",
    SentCodeType.MISSED_CALL: "code_via_missed_call",
    SentCodeType.FRAGMENT_SMS: "code_via_fragment",
    SentCodeType.EMAIL_CODE: "code_via_email",
}


def _where_text(sent_code, lang: str) -> str:
    """Kod qaysi kanal orqali yuborilganini tushuntiruvchi matn."""
    key = _CODE_TYPE_KEYS.get(getattr(sent_code, "type", None), "code_via_app")
    return get_text(key, lang)


async def _cleanup_client(state: FSMContext) -> None:
    """FSM data'sidagi Pyrogram clientni xavfsiz uzish."""
    try:
        data = await state.get_data()
        client: Client | None = data.get("client")
        if client is not None and client.is_connected:
            await client.disconnect()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# 1-BOSQICH: Akkauntni ulash tugmasi bosildi
# ═══════════════════════════════════════════════════════════════════════════

@router.message(F.text.in_({"🔗 Akkauntni ulash", "🔗 Аккаунтни улаш"}))
async def link_account_start(
    message: Message, state: FSMContext, lang: str = "uz_lat"
) -> None:
    """Akkaunt ulash jarayonini boshlash."""
    if not message.from_user:
        return

    telegram_id = message.from_user.id

    # Allaqachon ulangan tekshiruvi
    try:
        session = db.get_session_string(telegram_id)
        if session:
            await message.answer(
                get_text("already_linked", lang),
                reply_markup=main_menu_kb(lang, is_linked=True),
                parse_mode="HTML",
            )
            return
    except Exception as e:
        logger.error("Session tekshirishda xato: %s", e)

    # Oldingi tugallanmagan urinishdan qolgan clientni tozalash
    await _cleanup_client(state)
    await state.clear()

    await state.set_state(LoginStates.waiting_phone)
    await message.answer(
        get_text("enter_phone", lang),
        reply_markup=back_kb(lang),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Login oqimini bekor qilish («⬅️ Ortga» tugmasi bilan)
# ═══════════════════════════════════════════════════════════════════════════

@router.message(
    StateFilter(
        LoginStates.waiting_phone,
        LoginStates.waiting_code,
        LoginStates.waiting_2fa,
    ),
    F.text.in_({"⬅️ Ortga", "⬅️ Ортга"}),
)
async def cancel_login(
    message: Message, state: FSMContext, lang: str = "uz_lat", is_linked: bool = False
) -> None:
    """Login jarayonini bekor qilish va asosiy menyuga qaytish."""
    await _cleanup_client(state)
    await state.clear()
    await message.answer(
        get_text("main_menu", lang),
        reply_markup=main_menu_kb(lang, is_linked),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 2-BOSQICH: Telefon raqam qabul qilish
# ═══════════════════════════════════════════════════════════════════════════

@router.message(LoginStates.waiting_phone, F.text.regexp(r"^\+\d{10,15}$"))
async def receive_phone(
    message: Message, state: FSMContext, lang: str = "uz_lat"
) -> None:
    """Telefon raqamini qabul qilish va Pyrogram orqali kod yuborish."""
    if not message.from_user:
        return

    telegram_id = message.from_user.id
    phone = message.text.strip()

    client = Client(
        name=f"login_{telegram_id}",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True,
    )

    sent_code = None
    err_text: str | None = None
    try:
        await client.connect()
        sent_code = await client.send_code(phone)
    except ApiIdInvalid:
        logger.error("ApiIdInvalid — API_ID/API_HASH noto'g'ri (telegram_id=%d)", telegram_id)
        err_text = get_text("err_api_invalid", lang)
    except PhoneNumberInvalid:
        err_text = get_text("err_phone_invalid", lang)
    except PhoneNumberBanned:
        err_text = get_text("err_phone_banned", lang)
    except PhoneNumberFlood:
        err_text = get_text("err_phone_flood", lang)
    except FloodWait as e:
        err_text = get_text("err_flood_wait", lang).format(seconds=getattr(e, "value", e))
    except Exception as e:
        logger.exception("Kod yuborishda kutilmagan xato (telegram_id=%d)", telegram_id)
        err_text = get_text("login_failed", lang).format(error=str(e))

    # ── Xatolik bo'lsa — tozalash va xabar berish ────────────────────────────
    if err_text is not None:
        try:
            if client.is_connected:
                await client.disconnect()
        except Exception:
            pass
        await state.clear()
        await message.answer(
            err_text,
            reply_markup=main_menu_kb(lang, is_linked=False),
            parse_mode="HTML",
        )
        return

    # ── Muvaffaqiyat — kod yuborildi ─────────────────────────────────────────
    where = _where_text(sent_code, lang)
    await state.update_data(
        client=client,
        phone=phone,
        phone_code_hash=sent_code.phone_code_hash,
        entered_digits="",
        code_where=where,
    )
    await state.set_state(LoginStates.waiting_code)
    await message.answer(
        get_text("enter_code", lang).format(
            digits=CODE_LENGTH,
            entered=_format_entered("", CODE_LENGTH),
            where=where,
        ),
        reply_markup=code_input_kb(lang=lang),
        parse_mode="HTML",
    )


@router.message(LoginStates.waiting_phone)
async def invalid_phone(
    message: Message, state: FSMContext, lang: str = "uz_lat"
) -> None:
    """Telefon raqami noto'g'ri formatda kiritildi."""
    await message.answer(
        get_text("enter_phone", lang),
        reply_markup=back_kb(lang),
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 3-BOSQICH: Inline numpad orqali kod kiritish
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(LoginStates.waiting_code, F.data.startswith("code_"))
async def handle_code_input(
    callback: CallbackQuery, state: FSMContext, lang: str = "uz_lat"
) -> None:
    """Numpad tugmalari bosilganda — raqam qo'shish, tozalash yoki tasdiqlash."""
    if not callback.from_user or not callback.message:
        await callback.answer()
        return

    telegram_id = callback.from_user.id
    data = await state.get_data()
    entered = data.get("entered_digits", "")
    where = data.get("code_where", "")
    action = callback.data  # 'code_0'..'code_9', 'code_clear', 'code_confirm', 'code_resend'

    # ── Tozalash ────────────────────────────────────────────────────────────
    if action == "code_clear":
        await state.update_data(entered_digits="")
        await callback.message.edit_text(
            get_text("enter_code", lang).format(
                digits=CODE_LENGTH,
                entered=_format_entered("", CODE_LENGTH),
                where=where,
            ),
            reply_markup=code_input_kb(lang=lang),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    # ── Kodni qayta yuborish (boshqa kanal orqali) ───────────────────────────
    if action == "code_resend":
        client: Client | None = data.get("client")
        phone = data.get("phone", "")
        phone_code_hash = data.get("phone_code_hash", "")
        if client is None:
            await callback.answer(get_text("login_failed", lang).format(error="session expired"), show_alert=True)
            await state.clear()
            return
        try:
            new_code = await client.resend_code(phone, phone_code_hash)
            new_where = _where_text(new_code, lang)
            await state.update_data(
                phone_code_hash=new_code.phone_code_hash,
                entered_digits="",
                code_where=new_where,
            )
            await callback.message.edit_text(
                get_text("code_resent", lang) + "\n\n" +
                get_text("enter_code", lang).format(
                    digits=CODE_LENGTH,
                    entered=_format_entered("", CODE_LENGTH),
                    where=new_where,
                ),
                reply_markup=code_input_kb(lang=lang),
                parse_mode="HTML",
            )
            await callback.answer(get_text("code_resent_alert", lang), show_alert=True)
        except FloodWait as e:
            await callback.answer(
                get_text("err_flood_wait", lang).format(seconds=getattr(e, "value", e)),
                show_alert=True,
            )
        except Exception as e:
            logger.exception("Kodni qayta yuborishda xato (telegram_id=%d)", telegram_id)
            await callback.answer(get_text("login_failed", lang).format(error=str(e)), show_alert=True)
        return

    # ── Tasdiqlash ──────────────────────────────────────────────────────────
    if action == "code_confirm":
        if len(entered) < CODE_LENGTH:
            await callback.answer(
                f"Iltimos, {CODE_LENGTH} ta raqam kiriting!",
                show_alert=True,
            )
            return

        client: Client | None = data.get("client")
        phone = data.get("phone", "")
        phone_code_hash = data.get("phone_code_hash", "")

        if client is None:
            await state.clear()
            await callback.message.edit_text(
                get_text("login_failed", lang).format(error="session expired"),
                parse_mode="HTML",
            )
            await callback.answer()
            return

        try:
            await client.sign_in(
                phone_number=phone,
                phone_code_hash=phone_code_hash,
                phone_code=entered,
            )

            session_string = await client.export_session_string()
            db.set_session_string(telegram_id, session_string)
            try:
                await client.disconnect()
            except Exception:
                pass
            await state.clear()

            await callback.message.edit_text(
                get_text("login_success", lang),
                parse_mode="HTML",
            )
            await callback.message.answer(
                get_text("main_menu", lang),
                reply_markup=main_menu_kb(lang, is_linked=True),
                parse_mode="HTML",
            )
            await callback.answer()
            return

        except SessionPasswordNeeded:
            await state.set_state(LoginStates.waiting_2fa)
            await callback.message.edit_text(
                get_text("enter_2fa", lang),
                parse_mode="HTML",
            )
            await callback.answer()
            return

        except (PhoneCodeInvalid, PhoneCodeExpired):
            await state.update_data(entered_digits="")
            await callback.message.edit_text(
                get_text("code_wrong", lang) + "\n\n" +
                get_text("enter_code", lang).format(
                    digits=CODE_LENGTH,
                    entered=_format_entered("", CODE_LENGTH),
                    where=where,
                ),
                reply_markup=code_input_kb(lang=lang),
                parse_mode="HTML",
            )
            await callback.answer()
            return

        except Exception as e:
            logger.error("Sign-in xatosi (telegram_id=%d): %s", telegram_id, e)
            try:
                if client.is_connected:
                    await client.disconnect()
            except Exception:
                pass
            await state.clear()
            await callback.message.edit_text(
                get_text("login_failed", lang).format(error=str(e)),
                parse_mode="HTML",
            )
            await callback.answer()
            return

    # ── Raqam kiritish (code_0 ... code_9) ──────────────────────────────────
    digit = action.replace("code_", "")
    if digit.isdigit():
        if len(entered) >= CODE_LENGTH:
            await callback.answer(
                f"Kod {CODE_LENGTH} ta raqamdan iborat!",
                show_alert=False,
            )
            return

        entered += digit
        await state.update_data(entered_digits=entered)
        await callback.message.edit_text(
            get_text("enter_code", lang).format(
                digits=CODE_LENGTH,
                entered=_format_entered(entered, CODE_LENGTH),
                where=where,
            ),
            reply_markup=code_input_kb(entered, lang),
            parse_mode="HTML",
        )

    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════
# 4-BOSQICH: 2FA parol qabul qilish
# ═══════════════════════════════════════════════════════════════════════════

@router.message(LoginStates.waiting_2fa, F.text)
async def receive_2fa_password(
    message: Message, state: FSMContext, lang: str = "uz_lat"
) -> None:
    """Ikki bosqichli autentifikatsiya parolini qabul qilish."""
    if not message.from_user:
        return

    telegram_id = message.from_user.id
    data = await state.get_data()
    client: Client | None = data.get("client")
    password = (message.text or "").strip()

    if client is None:
        await state.clear()
        await message.answer(
            get_text("login_failed", lang).format(error="session expired"),
            reply_markup=main_menu_kb(lang, is_linked=False),
            parse_mode="HTML",
        )
        return

    try:
        await client.check_password(password)

        session_string = await client.export_session_string()
        db.set_session_string(telegram_id, session_string)
        try:
            await client.disconnect()
        except Exception:
            pass
        await state.clear()

        # Parol xabarini o'chirish (xavfsizlik uchun)
        try:
            await message.delete()
        except Exception:
            pass

        await message.answer(
            get_text("login_success", lang),
            reply_markup=main_menu_kb(lang, is_linked=True),
            parse_mode="HTML",
        )

    except BadRequest as e:
        logger.warning("2FA parol noto'g'ri (telegram_id=%d): %s", telegram_id, e)
        await message.answer(
            get_text("code_wrong", lang) + "\n" + get_text("enter_2fa", lang),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error("2FA xatosi (telegram_id=%d): %s", telegram_id, e)
        try:
            if client.is_connected:
                await client.disconnect()
        except Exception:
            pass
        await state.clear()
        await message.answer(
            get_text("login_failed", lang).format(error=str(e)),
            reply_markup=main_menu_kb(lang, is_linked=False),
            parse_mode="HTML",
        )
