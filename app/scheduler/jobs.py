"""
APScheduler ishlari (jobs).
broadcast_job – har 30 soniyada faol xabarlarni tekshiradi va yuboradi.

Holat o'zgarganda (sinov tugadi, obuna tugadi, vaqt tugadi, bloklandi)
broadcast to'xtatiladi va foydalanuvchi bot orqali ogohlantiriladi.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import SUPPORT_PHONE, SUPPORT_USERNAME
from app.database.supabase_client import db
from app.bot.bot import bot
from app.bot.texts import get_text
from app.userbot.sender import send_to_groups

logger = logging.getLogger(__name__)

# Sinov tugashiga oz qolganda ogohlantiriladigan chegara
TRIAL_LOW_THRESHOLD = 3


async def _notify(telegram_id: int, text: str) -> None:
    """Foydalanuvchiga bot orqali ogohlantirish yuboradi (xato bo'lsa e'tiborsiz)."""
    try:
        await bot.send_message(telegram_id, text, parse_mode="HTML")
    except Exception as e:
        logger.warning("Ogohlantirish yuborilmadi (user=%s): %s", telegram_id, e)


async def broadcast_job() -> None:
    """
    Asosiy broadcast ishi – har 30 soniyada ishlaydi.

    Jarayon:
        1. Barcha is_running=True xabarlarni olish
        2. Davomiylik tugagan bo'lsa – to'xtatish + ogohlantirish
        3. Interval yetarli bo'lmasa – o'tkazib yuborish
        4. Yuborish huquqi (trial/obuna/blok) tekshiruvi – muammo bo'lsa
           to'xtatish + ogohlantirish
        5. Yuborish + sinov tugaganda/tugashiga oz qolganda ogohlantirish
    """
    try:
        running_messages = db.get_running_messages()
    except Exception as e:
        logger.error("Faol xabarlarni olishda xato: %s", e)
        return

    if not running_messages:
        return

    now = datetime.now(timezone.utc)

    for msg in running_messages:
        telegram_id = msg.get("user_telegram_id")
        if not telegram_id:
            continue

        user_data = msg.get("users") or {}
        lang = user_data.get("language") or "uz_lat"

        try:
            # ── 1. Davomiylik tekshiruvi ─────────────────────────────────
            duration_hours = msg.get("duration_hours", 0)
            started_at = msg.get("started_running_at")

            if duration_hours and duration_hours > 0 and started_at:
                started_dt = datetime.fromisoformat(started_at)
                if started_dt.tzinfo is None:
                    started_dt = started_dt.replace(tzinfo=timezone.utc)
                elapsed_hours = (now - started_dt).total_seconds() / 3600

                if elapsed_hours >= duration_hours:
                    logger.info(
                        "Davomiylik tugadi, to'xtatilmoqda: user=%s", telegram_id
                    )
                    db.set_message_running(telegram_id, False)
                    await _notify(
                        telegram_id,
                        get_text("notify_duration_done", lang).format(hours=duration_hours),
                    )
                    continue

            # ── 2. Interval tekshiruvi ───────────────────────────────────
            interval_minutes = msg.get("interval_minutes", 2)
            last_sent_at = msg.get("last_sent_at")

            if last_sent_at:
                last_dt = datetime.fromisoformat(last_sent_at)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                elapsed_minutes = (now - last_dt).total_seconds() / 60
                if elapsed_minutes < interval_minutes:
                    continue

            # ── 3. Yuborish huquqi tekshiruvi ────────────────────────────
            can_send, reason = db.can_send_message(telegram_id)
            if not can_send:
                # Vaqtinchalik xabar bloki — to'xtatmaymiz, muddat tugagach
                # avtomatik davom etadi.
                if reason == "msg_blocked":
                    continue

                # Boshqa sabablar — broadcastni to'xtatamiz va ogohlantiramiz
                db.set_message_running(telegram_id, False)

                if reason == "trial_expired":
                    if user_data.get("subscription_end"):
                        # Avval obuna bo'lgan, endi tugagan
                        text = get_text("notify_subscription_expired", lang).format(
                            support_phone=SUPPORT_PHONE,
                            support_username=SUPPORT_USERNAME,
                        )
                    else:
                        text = get_text("notify_trial_expired", lang).format(
                            support_phone=SUPPORT_PHONE,
                            support_username=SUPPORT_USERNAME,
                        )
                elif reason == "blocked":
                    text = get_text("notify_blocked", lang).format(
                        support_username=SUPPORT_USERNAME,
                    )
                else:
                    text = get_text("notify_stopped", lang)

                await _notify(telegram_id, text)
                logger.info(
                    "Broadcast to'xtatildi (user=%s, sabab=%s)", telegram_id, reason
                )
                continue

            # ── 4. Yuborish ──────────────────────────────────────────────
            logger.info("Broadcast boshlanmoqda: user=%s", telegram_id)
            result = await send_to_groups(telegram_id, reason)
            logger.info(
                "Broadcast natijasi: user=%s, sent=%d, failed=%d",
                telegram_id, result["sent"], result["failed"],
            )

            # ── 5. Sinov holati bo'yicha ogohlantirish ───────────────────
            if reason == "trial":
                trial_left = result.get("trial_left")
                if trial_left == 0:
                    db.set_message_running(telegram_id, False)
                    await _notify(
                        telegram_id,
                        get_text("notify_trial_expired", lang).format(
                            support_phone=SUPPORT_PHONE,
                            support_username=SUPPORT_USERNAME,
                        ),
                    )
                    logger.info("Sinov tugadi, to'xtatildi: user=%s", telegram_id)
                elif trial_left is not None and trial_left <= TRIAL_LOW_THRESHOLD and trial_left > 0:
                    await _notify(
                        telegram_id,
                        get_text("notify_trial_low", lang).format(
                            left=trial_left,
                            support_username=SUPPORT_USERNAME,
                        ),
                    )

        except Exception as e:
            logger.error("Broadcast xatosi: user=%s, err=%s", telegram_id, e)


def setup_scheduler() -> AsyncIOScheduler:
    """
    AsyncIOScheduler yaratadi va sozlaydi.

    Returns:
        Sozlangan scheduler obyekti.
    """
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        broadcast_job,
        trigger="interval",
        seconds=30,
        id="broadcast_job",
        name="Broadcast – xabar yuborish",
        replace_existing=True,
        max_instances=1,
    )
    logger.info("APScheduler sozlandi: broadcast_job har 30 soniyada")
    return scheduler
