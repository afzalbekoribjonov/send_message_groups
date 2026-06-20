"""
APScheduler ishlari (jobs).
broadcast_job – har 30 soniyada faol xabarlarni tekshiradi va yuboradi.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database.supabase_client import db
from app.userbot.sender import send_to_groups

logger = logging.getLogger(__name__)


async def broadcast_job() -> None:
    """
    Asosiy broadcast ishi – har 30 soniyada ishlaydi.

    Jarayon:
        1. Barcha is_running=True xabarlarni olish
        2. Har biri uchun interval va duration tekshiruvi
        3. Agar duration tugagan bo'lsa – to'xtatish
        4. Agar interval yetarli bo'lsa – yuborish
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

        try:
            # ── Duration tekshiruvi ──────────────────────────────────────
            duration_hours = msg.get("duration_hours", 0)
            started_at = msg.get("started_running_at")

            if duration_hours and duration_hours > 0 and started_at:
                started_dt = datetime.fromisoformat(started_at)
                # timezone-naive bo'lsa UTC deb qabul qilamiz
                if started_dt.tzinfo is None:
                    started_dt = started_dt.replace(tzinfo=timezone.utc)
                elapsed_hours = (now - started_dt).total_seconds() / 3600

                if elapsed_hours >= duration_hours:
                    logger.info(
                        "Duration tugadi, to'xtatilmoqda: user=%s, "
                        "elapsed=%.1fh, duration=%dh",
                        telegram_id, elapsed_hours, duration_hours,
                    )
                    db.set_message_running(telegram_id, False)
                    continue

            # ── Interval tekshiruvi ──────────────────────────────────────
            interval_minutes = msg.get("interval_minutes", 2)
            last_sent_at = msg.get("last_sent_at")

            if last_sent_at:
                last_dt = datetime.fromisoformat(last_sent_at)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                elapsed_minutes = (now - last_dt).total_seconds() / 60

                if elapsed_minutes < interval_minutes:
                    # Hali vaqt yetmagan
                    continue

            # ── Yuborish ─────────────────────────────────────────────────
            logger.info("Broadcast boshlanmoqda: user=%s", telegram_id)
            result = await send_to_groups(telegram_id)
            logger.info(
                "Broadcast natijasi: user=%s, sent=%d, failed=%d",
                telegram_id, result["sent"], result["failed"],
            )

        except Exception as e:
            logger.error(
                "Broadcast xatosi: user=%s, err=%s", telegram_id, e
            )


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
