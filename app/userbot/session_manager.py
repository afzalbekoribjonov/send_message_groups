"""
Pyrogram session boshqaruvchisi.
Foydalanuvchining session_string'i orqali Pyrogram Client yaratadi.
"""

import logging
from typing import Optional

from pyrogram import Client

from app.config import API_ID, API_HASH
from app.database.supabase_client import db

logger = logging.getLogger(__name__)


async def get_client(telegram_id: int) -> Optional[Client]:
    """
    Berilgan telegram_id uchun Pyrogram Client yaratadi.
    Session string ma'lumotlar bazasidan olinadi.

    Returns:
        Client obyekti yoki None (agar session topilmasa).
    """
    session_string = db.get_session_string(telegram_id)
    if not session_string:
        logger.warning("Session string topilmadi: telegram_id=%s", telegram_id)
        return None

    client = Client(
        name=f"user_{telegram_id}",
        session_string=session_string,
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True,
    )
    return client


async def create_temp_client() -> Client:
    """
    Vaqtinchalik Pyrogram Client yaratadi (login jarayoni uchun).
    Bu klient hali session_string bilan bog'lanmagan.
    """
    client = Client(
        name="temp_login",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True,
    )
    return client
