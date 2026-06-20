"""
Aiogram FSM holatlari (states).

Stateful oqimlar (login, reklama matni kiritish, sozlamalar) faqat mos
holatda ishlovchi handler'lar orqali boshqariladi. Bu blanket `F.text`
handler'larining boshqa tugmalarni "yutib yuborishi" muammosini butunlay
oldini oladi.
"""

from aiogram.fsm.state import State, StatesGroup


class LoginStates(StatesGroup):
    """Akkauntni ulash jarayoni holatlari."""
    waiting_phone = State()   # Telefon raqamini kutmoqda
    waiting_code = State()    # Tasdiqlash kodini kutmoqda (inline numpad)
    waiting_2fa = State()     # Ikki bosqichli parolni kutmoqda


class AdStates(StatesGroup):
    """Reklama matnini kiritish holati."""
    waiting_text = State()


class SettingsStates(StatesGroup):
    """Sozlamalar — interval va davomiylik kiritish holatlari."""
    waiting_interval = State()
    waiting_duration = State()
