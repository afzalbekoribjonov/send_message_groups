"""
Reply (oddiy) klaviaturalar — asosiy menyu, til tanlash, sozlamalar, ortga.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.bot.texts import get_text


def language_kb() -> ReplyKeyboardMarkup:
    """Til tanlash klaviaturasi (birinchi marta /start bosilganda)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 O'zbekcha (Lotin)"),
                KeyboardButton(text="🇺🇿 Ўзбекча (Кирилл)"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_kb(
    lang: str = "uz_lat", is_linked: bool = False, is_running: bool = False
) -> ReplyKeyboardMarkup:
    """Asosiy menyu — akkaunt holatiga qarab tegishli tugmalarni qaytaradi.

    Tarqatish tugmasi bitta bo'lib, holatga qarab o'zgaradi:
    ishlayotgan bo'lsa «To'xtatish», aks holda «Boshlash».
    """
    if is_linked:
        broadcast_btn = (
            get_text("btn_stop_broadcast", lang)
            if is_running
            else get_text("btn_start_broadcast", lang)
        )
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=get_text("btn_ad_text", lang)),
                    KeyboardButton(text=get_text("btn_groups", lang)),
                ],
                [
                    KeyboardButton(text=broadcast_btn),
                ],
                [
                    KeyboardButton(text=get_text("btn_stats", lang)),
                    KeyboardButton(text=get_text("btn_settings", lang)),
                ],
                [
                    KeyboardButton(text=get_text("btn_help", lang)),
                ],
            ],
            resize_keyboard=True,
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=get_text("btn_link_account", lang)),
                ],
                [
                    KeyboardButton(text=get_text("btn_settings", lang)),
                    KeyboardButton(text=get_text("btn_help", lang)),
                ]
            ],
            resize_keyboard=True,
        )


def settings_kb(lang: str = "uz_lat", is_linked: bool = False) -> ReplyKeyboardMarkup:
    """Sozlamalar pastki menyusi."""
    kb = [
        [
            KeyboardButton(text=get_text("btn_lang_lat", lang)),
            KeyboardButton(text=get_text("btn_lang_cyr", lang)),
        ]
    ]
    if is_linked:
        kb.insert(0, [
            KeyboardButton(text=get_text("btn_interval", lang)),
            KeyboardButton(text=get_text("btn_duration", lang)),
        ])
        kb.append([
            KeyboardButton(text=get_text("btn_logout", lang)),
        ])
    kb.append([
        KeyboardButton(text=get_text("btn_back", lang)),
    ])
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )


def back_kb(lang: str = "uz_lat") -> ReplyKeyboardMarkup:
    """Faqat 'Ortga' tugmasi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text("btn_back", lang))],
        ],
        resize_keyboard=True,
    )
