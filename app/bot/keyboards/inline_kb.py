"""
Inline klaviaturalar — kod kiritish numpad, guruhlar toggle, statistika boshqaruvi.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.bot.texts import get_text


def stats_kb(lang: str = "uz_lat", is_running: bool = False) -> InlineKeyboardMarkup:
    """Statistika xabari ostidagi boshqaruv tugmalari.

    is_running holatiga qarab «To'xtatish» yoki «Boshlash» ko'rsatadi.
    """
    if is_running:
        toggle = InlineKeyboardButton(
            text=get_text("btn_stats_stop", lang), callback_data="bc_stop"
        )
    else:
        toggle = InlineKeyboardButton(
            text=get_text("btn_stats_start", lang), callback_data="bc_start"
        )
    return InlineKeyboardMarkup(inline_keyboard=[
        [toggle],
        [
            InlineKeyboardButton(text=get_text("btn_stats_refresh", lang), callback_data="stats_refresh"),
            InlineKeyboardButton(text=get_text("btn_stats_close", lang), callback_data="stats_close"),
        ],
    ])


def code_input_kb(current_code: str = "", lang: str = "uz_lat") -> InlineKeyboardMarkup:
    """Tasdiqlash kodini kiritish uchun numpad klaviatura.

    Har bir raqam tugmasining callback_data = 'code_X' formatida.
    ❌ — tozalash (code_clear), ✅ — tasdiqlash (code_confirm),
    🔁 — kodni qayta yuborish (code_resend).

    Args:
        current_code: hozircha kiritilgan raqamlar (faqat holatni track qilish uchun).
        lang: til kodi (qayta yuborish tugmasi matni uchun).
    """
    rows = [
        # 1-qator: 1, 2, 3
        [
            InlineKeyboardButton(text="1", callback_data="code_1"),
            InlineKeyboardButton(text="2", callback_data="code_2"),
            InlineKeyboardButton(text="3", callback_data="code_3"),
        ],
        # 2-qator: 4, 5, 6
        [
            InlineKeyboardButton(text="4", callback_data="code_4"),
            InlineKeyboardButton(text="5", callback_data="code_5"),
            InlineKeyboardButton(text="6", callback_data="code_6"),
        ],
        # 3-qator: 7, 8, 9
        [
            InlineKeyboardButton(text="7", callback_data="code_7"),
            InlineKeyboardButton(text="8", callback_data="code_8"),
            InlineKeyboardButton(text="9", callback_data="code_9"),
        ],
        # 4-qator: ❌ tozalash, 0, ✅ tasdiqlash
        [
            InlineKeyboardButton(text="❌", callback_data="code_clear"),
            InlineKeyboardButton(text="0", callback_data="code_0"),
            InlineKeyboardButton(text="✅", callback_data="code_confirm"),
        ],
        # 5-qator: kod kelmadimi? qayta yuborish
        [
            InlineKeyboardButton(text=get_text("btn_resend_code", lang), callback_data="code_resend"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_logout_kb(lang: str = "uz_lat") -> InlineKeyboardMarkup:
    """Hisobdan chiqishni tasdiqlash — Ha / Yo'q."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_yes", lang), callback_data="logout_yes"),
            InlineKeyboardButton(text=get_text("btn_no", lang), callback_data="logout_no"),
        ],
    ])


from aiogram.types import WebAppInfo

def groups_webapp_kb(lang: str = "uz_lat") -> InlineKeyboardMarkup:
    """Guruhlarni boshqarish uchun WebApp tugmasi."""
    from app.config import WEBAPP_URL
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=get_text("btn_groups", lang) + " 🛠",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ])
