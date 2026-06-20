"""
/start buyrug'i va til tanlash handler'i.

Til mantiqi:
  • Birinchi marta /start bosilganda (til hali tanlanmagan) — til tanlash so'raladi.
  • Til tanlangach va keyingi /start larda — to'g'ridan-to'g'ri asosiy menyu.
  • Tilni keyinchalik «⚙️ Sozlamalar» orqali o'zgartirish mumkin (xuddi shu
    tugma matnlari bu yerda ham tutiladi, shuning uchun sozlamalardan
    o'zgartirish ham ishlaydi).
"""

import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database.supabase_client import db
from app.bot.texts import get_text
from app.bot.keyboards.reply_kb import language_kb, main_menu_kb

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    user: dict | None = None,
    lang: str = "uz_lat",
    is_linked: bool = False,
    is_running: bool = False,
) -> None:
    """/start — foydalanuvchini ro'yxatdan o'tkazadi.

    Til allaqachon tanlangan bo'lsa to'g'ridan-to'g'ri asosiy menyuni,
    aks holda til tanlash klaviaturasini ko'rsatadi.

    `user` — middleware allaqachon bazadan o'qigan ma'lumot (qayta so'ralmaydi).
    """
    if not message.from_user:
        return

    # Har qanday yarim qolgan holatni tozalaymiz
    await state.clear()

    telegram_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    language_chosen = False
    try:
        if not user:
            db.create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
            )
            logger.info("Yangi foydalanuvchi: %s (%d)", username, telegram_id)
        else:
            # Mavjud foydalanuvchi — username yoki ism o'zgargandagina yangilaymiz
            # (har bir /start da ortiqcha yozuvni oldini olish uchun)
            if user.get("username") != username or user.get("first_name") != first_name:
                db.update_user(telegram_id, username=username, first_name=first_name)
            language_chosen = bool(user.get("language"))
            is_linked = bool(user.get("session_string"))
    except Exception as e:
        logger.error("Foydalanuvchini yaratishda xato: %s", e)

    # Til allaqachon tanlangan — to'g'ridan-to'g'ri asosiy menyu
    if language_chosen:
        await message.answer(
            get_text("main_menu", lang),
            reply_markup=main_menu_kb(lang, is_linked, is_running),
            parse_mode="HTML",
        )
        return

    # Birinchi marta — til tanlashni so'raymiz
    await message.answer(
        get_text("welcome", lang),
        reply_markup=language_kb(),
        parse_mode="HTML",
    )


async def _apply_language(
    message: Message,
    state: FSMContext,
    lang: str,
    is_linked: bool,
) -> None:
    """Tanlangan tilni saqlash va asosiy menyuni ko'rsatish.

    Birinchi tanlovda ham, sozlamalardan o'zgartirishda ham ishlaydi.
    """
    if not message.from_user:
        return

    await state.clear()
    telegram_id = message.from_user.id
    is_running = False

    try:
        db.set_user_language(telegram_id, lang)
        # is_linked qiymatini bazadan aniqlaymiz (boshlang'ich /start da
        # middleware uni hali bilmasligi mumkin, shuning uchun xavfsizroq)
        user = db.get_user(telegram_id)
        is_linked = bool(user and user.get("session_string"))
        if is_linked:
            user_msg = db.get_user_message(telegram_id)
            is_running = bool(user_msg and user_msg.get("is_running"))
    except Exception as e:
        logger.error("Tilni saqlashda xato: %s", e)

    await message.answer(
        get_text("language_changed", lang),
        parse_mode="HTML",
    )
    await message.answer(
        get_text("main_menu", lang),
        reply_markup=main_menu_kb(lang, is_linked, is_running),
        parse_mode="HTML",
    )


@router.message(F.text == "🇺🇿 O'zbekcha (Lotin)")
async def select_lang_lat(
    message: Message, state: FSMContext, is_linked: bool = False
) -> None:
    """O'zbek-Lotin tili tanlandi."""
    await _apply_language(message, state, "uz_lat", is_linked)


@router.message(F.text == "🇺🇿 Ўзбекча (Кирилл)")
async def select_lang_cyr(
    message: Message, state: FSMContext, is_linked: bool = False
) -> None:
    """O'zbek-Kirill tili tanlandi."""
    await _apply_language(message, state, "uz_cyr", is_linked)
