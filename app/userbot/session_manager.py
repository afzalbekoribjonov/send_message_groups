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


active_clients: dict[int, Client] = {}

async def get_client(telegram_id: int) -> Optional[Client]:
    """
    Berilgan telegram_id uchun Pyrogram Client yaratadi yoki mavjudini qaytaradi.
    """
    if telegram_id in active_clients:
        client = active_clients[telegram_id]
        if not client.is_connected:
            try:
                await client.start()
            except Exception:
                pass
        return client

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
    
    try:
        await client.start()
        # Birinchi marta ishga tushganda keshni to'ldiramiz
        async for _ in client.get_dialogs(limit=500):
            pass
    except Exception as e:
        logger.error("Client start xatosi: %s", e)
        
    active_clients[telegram_id] = client
    return client

async def stop_client(telegram_id: int):
    """Clientni to'xtatish va keshdan o'chirish."""
    if telegram_id in active_clients:
        client = active_clients.pop(telegram_id)
        try:
            if client.is_connected:
                await client.stop()
        except Exception:
            pass


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
