"""
Xabar yuborish moduli.
Foydalanuvchining reklama xabarini barcha faol guruhlariga yuboradi.
FloodWait, trial/subscription tekshiruvlari, statistika boshqaruvi.
"""

import asyncio
import logging
import random

from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, ChatWriteForbidden, PeerIdInvalid

from app.config import JITTER_MIN_SECONDS, JITTER_MAX_SECONDS
from app.database.supabase_client import db
from app.userbot.session_manager import get_client

logger = logging.getLogger(__name__)


async def send_to_groups(telegram_id: int, reason: str = "trial") -> dict:
    """
    Foydalanuvchining reklama xabarini barcha faol guruhlariga yuboradi.

    Ruxsat tekshiruvi (trial/obuna/blok) bu yerda emas, chaqiruvchi (scheduler
    job) tomonida amalga oshiriladi — shunda holat o'zgarganda foydalanuvchi
    ogohlantiriladi va broadcast to'xtatiladi.

    Args:
        telegram_id: Foydalanuvchining Telegram ID'si.
        reason: Yuborish asosi ("trial" yoki "subscribed"). "trial" bo'lsa
                muvaffaqiyatli yuborilgach sinov xabarlari soni kamaytiriladi.

    Returns:
        dict: {sent, failed, errors, trial_left}
              trial_left — sinov kamaytirilgan bo'lsa qolgan miqdor, aks holda None.
    """
    stats = {"sent": 0, "failed": 0, "errors": [], "trial_left": None}

    # ── 2. Xabar matnini olish ───────────────────────────────────────────────
    msg_data = db.get_user_message(telegram_id)
    if not msg_data or not msg_data.get("message_text"):
        stats["errors"].append("Reklama xabari topilmadi")
        return stats

    message_text = msg_data["message_text"]

    # ── 3. Faol guruhlarni olish ─────────────────────────────────────────────
    groups = db.get_active_groups(telegram_id)
    if not groups:
        stats["errors"].append("Faol guruhlar topilmadi")
        return stats

    # ── 4. Pyrogram client yaratish ──────────────────────────────────────────
    client = await get_client(telegram_id)
    if client is None:
        stats["errors"].append("Session string topilmadi")
        return stats

    # ── 5. Xabarlarni yuborish ───────────────────────────────────────────────
    try:
        await client.start()

        # Pyrogram peer keshini to'ldirish.
        # Yangi session_string'dan ishga tushgan client guruhlarning access_hash'ini
        # bilmaydi — natijada send_message(chat_id) "PeerIdInvalid" xatosini beradi.
        # get_dialogs() bir marta aylanib chiqilsa, barcha peerlar keshga yoziladi.
        try:
            async for _ in client.get_dialogs():
                pass
        except Exception as e:
            logger.warning("Peer keshini to'ldirishda ogohlantirish (user=%s): %s", telegram_id, e)

        for i, group in enumerate(groups):
            chat_id = group["chat_id"]
            try:
                await client.send_message(chat_id, message_text, parse_mode=ParseMode.HTML)
                db.increment_sent(telegram_id)
                stats["sent"] += 1
                logger.info(
                    "Xabar yuborildi: user=%s, chat=%s", telegram_id, chat_id
                )
            except FloodWait as e:
                wait_time = e.value
                logger.warning(
                    "FloodWait: %s soniya kutish, user=%s", wait_time, telegram_id
                )
                stats["errors"].append(
                    f"FloodWait: {wait_time}s kutish (chat={chat_id})"
                )
                await asyncio.sleep(wait_time)
                # Qayta urinish
                try:
                    await client.send_message(chat_id, message_text, parse_mode=ParseMode.HTML)
                    db.increment_sent(telegram_id)
                    stats["sent"] += 1
                except Exception as retry_err:
                    db.increment_failed(telegram_id)
                    stats["failed"] += 1
                    stats["errors"].append(f"Qayta urinish xato: {retry_err}")
            except ChatWriteForbidden:
                db.increment_failed(telegram_id)
                stats["failed"] += 1
                stats["errors"].append(
                    f"Guruhga yozish taqiqlangan: {chat_id}"
                )
                logger.warning(
                    "ChatWriteForbidden: user=%s, chat=%s", telegram_id, chat_id
                )
            except PeerIdInvalid:
                db.increment_failed(telegram_id)
                stats["failed"] += 1
                stats["errors"].append(f"Noto'g'ri guruh: {chat_id}")
                logger.warning(
                    "PeerIdInvalid: user=%s, chat=%s", telegram_id, chat_id
                )
            except Exception as e:
                db.increment_failed(telegram_id)
                stats["failed"] += 1
                stats["errors"].append(f"Xato ({chat_id}): {e}")
                logger.error(
                    "Xabar yuborishda xato: user=%s, chat=%s, err=%s",
                    telegram_id, chat_id, e,
                )

            # Guruhlar orasida random kechikish (oxirgi guruhdan keyin kutmaslik)
            if i < len(groups) - 1:
                jitter = random.uniform(JITTER_MIN_SECONDS, JITTER_MAX_SECONDS)
                await asyncio.sleep(jitter)

    except Exception as e:
        stats["errors"].append(f"Client xatosi: {e}")
        logger.error("Client xatosi: user=%s, err=%s", telegram_id, e)
    finally:
        try:
            await client.stop()
        except Exception:
            pass

    # ── 6. Trial xabarni kamaytirish ────────────────────────────────────────
    if reason == "trial" and stats["sent"] > 0:
        stats["trial_left"] = db.decrement_trial(telegram_id)

    # ── 7. last_sent vaqtini yangilash ───────────────────────────────────────
    if stats["sent"] > 0:
        db.set_last_sent(telegram_id)

    logger.info(
        "Yuborish yakunlandi: user=%s, sent=%d, failed=%d",
        telegram_id, stats["sent"], stats["failed"],
    )
    return stats
