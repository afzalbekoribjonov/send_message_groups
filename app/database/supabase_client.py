"""
Supabase ma'lumotlar bazasi bilan ishlash uchun CRUD operatsiyalari.
Barcha jadvallar: users, user_groups, user_messages, statistics, system_admins.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from supabase import create_client, Client

from app.config import SUPABASE_URL, SUPABASE_KEY, FREE_TRIAL_MESSAGES

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Supabase bilan ishlash uchun asosiy klass."""

    def __init__(self) -> None:
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return self._client

    # ─────────────────────────────────────────────────────────────────────────
    # USERS (Foydalanuvchilar)
    # ─────────────────────────────────────────────────────────────────────────

    def get_user(self, telegram_id: int) -> Optional[dict]:
        """Foydalanuvchini telegram_id bo'yicha olish."""
        result = (
            self.client.table("users")
            .select("*")
            .eq("telegram_id", telegram_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def create_user(self, telegram_id: int, username: str = "",
                    first_name: str = "", language: Optional[str] = None) -> dict:
        """Yangi foydalanuvchi yaratish.

        language=None — til hali tanlanmaganligini bildiradi. /start birinchi
        marta bosilganda til tanlash so'raladi, keyin esa to'g'ridan-to'g'ri
        asosiy menyu ko'rsatiladi.
        """
        data = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "language": language,
            "status": "new",
            "trial_messages_left": FREE_TRIAL_MESSAGES,
        }
        result = self.client.table("users").upsert(data).execute()
        return result.data[0] if result.data else data

    def update_user(self, telegram_id: int, **fields: Any) -> Optional[dict]:
        """Foydalanuvchi ma'lumotlarini yangilash."""
        result = (
            self.client.table("users")
            .update(fields)
            .eq("telegram_id", telegram_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def set_session_string(self, telegram_id: int, session_string: str) -> None:
        """Pyrogram session string saqlash."""
        self.update_user(telegram_id, session_string=session_string, status="active")

    def get_session_string(self, telegram_id: int) -> Optional[str]:
        """Pyrogram session string olish."""
        user = self.get_user(telegram_id)
        return user.get("session_string") if user else None

    def set_user_language(self, telegram_id: int, language: str) -> None:
        """Foydalanuvchi tilini o'zgartirish."""
        self.update_user(telegram_id, language=language)

    def get_all_users(self) -> list[dict]:
        """Barcha foydalanuvchilarni olish (admin panel uchun)."""
        result = self.client.table("users").select("*").order("created_at", desc=True).execute()
        return result.data or []

    def get_active_users(self) -> list[dict]:
        """Faol foydalanuvchilarni olish."""
        result = (
            self.client.table("users")
            .select("*")
            .eq("status", "active")
            .execute()
        )
        return result.data or []

    def block_user(self, telegram_id: int) -> None:
        """Foydalanuvchini butunlay bloklash (admin blokdan chiqarmaguncha)."""
        self.update_user(telegram_id, status="blocked")

    def unblock_user(self, telegram_id: int) -> None:
        """Foydalanuvchini blokdan chiqarish.

        Akkaunt ulangan bo'lsa 'active', aks holda 'new' holatiga qaytaradi.
        Barcha vaqtinchalik cheklovlarni ham tozalaydi.
        """
        user = self.get_user(telegram_id)
        new_status = "active" if (user and user.get("session_string")) else "new"
        self.update_user(
            telegram_id,
            status=new_status,
            blocked_until=None,
            msg_blocked_until=None,
        )

    def temp_block_user(self, telegram_id: int, until: datetime) -> None:
        """Foydalanuvchini vaqtinchalik bloklash (holatni o'zgartirmasdan).

        blocked_until tugagach foydalanuvchi avtomatik ravishda yana xabar
        yubora oladi (can_send_message tekshiradi).
        """
        self.update_user(telegram_id, blocked_until=until.isoformat())

    def block_user_messages(self, telegram_id: int, until: datetime) -> None:
        """Xabar yuborishni vaqtinchalik bloklash."""
        self.update_user(telegram_id, msg_blocked_until=until.isoformat())

    def unblock_user_messages(self, telegram_id: int) -> None:
        """Xabar yuborish cheklovini olib tashlash."""
        self.update_user(telegram_id, msg_blocked_until=None)

    def set_subscription(self, telegram_id: int, end_date: datetime) -> None:
        """Obuna muddatini aniq sanaga belgilash (qayta yozish)."""
        self.update_user(telegram_id, subscription_end=end_date.isoformat())

    def extend_subscription(self, telegram_id: int, days: int) -> datetime:
        """Obunani uzaytirish.

        Agar amaldagi obuna hali tugamagan bo'lsa — uning ustiga qo'shadi,
        aks holda hozirgi vaqtdan boshlab hisoblaydi. Yangi tugash sanasini
        qaytaradi.
        """
        now = datetime.now(timezone.utc)
        user = self.get_user(telegram_id)
        base = now
        if user and user.get("subscription_end"):
            try:
                current = datetime.fromisoformat(user["subscription_end"])
                if current.tzinfo is None:
                    current = current.replace(tzinfo=timezone.utc)
                if current > now:
                    base = current
            except (ValueError, TypeError):
                base = now
        new_end = base + timedelta(days=days)
        self.update_user(telegram_id, subscription_end=new_end.isoformat())
        return new_end

    def remove_subscription(self, telegram_id: int) -> None:
        """Obunani bekor qilish."""
        self.update_user(telegram_id, subscription_end=None)

    def set_trial(self, telegram_id: int, count: int) -> None:
        """Bepul sinov xabarlari sonini belgilash."""
        self.update_user(telegram_id, trial_messages_left=max(0, count))

    def delete_user(self, telegram_id: int) -> None:
        """Foydalanuvchini va u bilan bog'liq barcha ma'lumotlarni o'chirish.

        FK ON DELETE CASCADE tufayli guruhlar, xabarlar va statistika ham
        avtomatik o'chiriladi.
        """
        self.client.table("users").delete().eq("telegram_id", telegram_id).execute()

    def decrement_trial(self, telegram_id: int, count: int = 1) -> int:
        """Bepul sinov xabarini kamaytirish. Qolgan miqdorni qaytaradi."""
        user = self.get_user(telegram_id)
        if not user:
            return 0
        left = max(0, user.get("trial_messages_left", 0) - count)
        self.update_user(telegram_id, trial_messages_left=left)
        return left

    @staticmethod
    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        """ISO sanani timezone-aware datetime'ga aylantiradi (naive bo'lsa UTC)."""
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def can_send_message(self, telegram_id: int) -> tuple[bool, str]:
        """Foydalanuvchi xabar yuborishi mumkinmi? (bool, sabab)."""
        user = self.get_user(telegram_id)
        if not user:
            return False, "user_not_found"
        if user.get("status") == "blocked":
            return False, "blocked"
        now = datetime.now(timezone.utc)
        # Umumiy (vaqtinchalik) bloklash
        blocked_dt = self._parse_dt(user.get("blocked_until"))
        if blocked_dt and now < blocked_dt:
            return False, "blocked"
        # Xabar bloklash
        msg_dt = self._parse_dt(user.get("msg_blocked_until"))
        if msg_dt and now < msg_dt:
            return False, "msg_blocked"
        # Obuna tekshiruvi
        sub_dt = self._parse_dt(user.get("subscription_end"))
        if sub_dt and now < sub_dt:
            return True, "subscribed"
        # Trial tekshiruvi
        trial_left = user.get("trial_messages_left", 0)
        if trial_left > 0:
            return True, "trial"
        return False, "trial_expired"

    # ─────────────────────────────────────────────────────────────────────────
    # USER GROUPS (Foydalanuvchi guruhlari)
    # ─────────────────────────────────────────────────────────────────────────

    def get_user_groups(self, telegram_id: int) -> list[dict]:
        """Foydalanuvchining guruhlarini olish."""
        result = (
            self.client.table("user_groups")
            .select("*")
            .eq("user_telegram_id", telegram_id)
            .execute()
        )
        return result.data or []

    def get_active_groups(self, telegram_id: int) -> list[dict]:
        """Foydalanuvchining faol guruhlarini olish."""
        result = (
            self.client.table("user_groups")
            .select("*")
            .eq("user_telegram_id", telegram_id)
            .eq("is_active", True)
            .execute()
        )
        return result.data or []

    def add_user_group(self, telegram_id: int, chat_id: int,
                       group_title: str = "") -> dict:
        """Guruh qo'shish."""
        data = {
            "user_telegram_id": telegram_id,
            "chat_id": chat_id,
            "group_title": group_title,
            "is_active": True,
        }
        result = self.client.table("user_groups").insert(data).execute()
        return result.data[0] if result.data else data

    def remove_user_group(self, group_id: str) -> None:
        """Guruhni o'chirish."""
        self.client.table("user_groups").delete().eq("id", group_id).execute()

    def toggle_group(self, group_id: str, is_active: bool) -> None:
        """Guruhni yoqish/o'chirish."""
        self.client.table("user_groups").update(
            {"is_active": is_active}
        ).eq("id", group_id).execute()

    def sync_user_groups(self, telegram_id: int,
                         groups: list[dict[str, Any]]) -> None:
        """Foydalanuvchi guruhlarini sinxronlashtirish.
        groups: [{"chat_id": ..., "title": ...}, ...]
        """
        existing = self.get_user_groups(telegram_id)
        existing_ids = {g["chat_id"] for g in existing}
        for g in groups:
            if g["chat_id"] not in existing_ids:
                self.add_user_group(telegram_id, g["chat_id"], g.get("title", ""))

    # ─────────────────────────────────────────────────────────────────────────
    # USER MESSAGES (Reklama xabarlari)
    # ─────────────────────────────────────────────────────────────────────────

    def get_user_message(self, telegram_id: int) -> Optional[dict]:
        """Foydalanuvchining reklama xabarini olish."""
        result = (
            self.client.table("user_messages")
            .select("*")
            .eq("user_telegram_id", telegram_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def set_user_message(self, telegram_id: int, message_text: str,
                         interval_minutes: int = 2,
                         duration_hours: int = 0) -> dict:
        """Reklama xabarini saqlash yoki yangilash."""
        existing = self.get_user_message(telegram_id)
        data = {
            "user_telegram_id": telegram_id,
            "message_text": message_text,
            "interval_minutes": max(2, interval_minutes),
            "duration_hours": duration_hours,
        }
        if existing:
            result = (
                self.client.table("user_messages")
                .update(data)
                .eq("id", existing["id"])
                .execute()
            )
        else:
            result = self.client.table("user_messages").insert(data).execute()
        return result.data[0] if result.data else data

    def update_message_settings(self, telegram_id: int, **fields: Any) -> None:
        """Xabar sozlamalarini yangilash (qator mavjud bo'lsa)."""
        existing = self.get_user_message(telegram_id)
        if existing:
            self.client.table("user_messages").update(fields).eq(
                "id", existing["id"]
            ).execute()

    def upsert_message_settings(self, telegram_id: int, **fields: Any) -> None:
        """Xabar sozlamalarini yangilash yoki yo'q bo'lsa yangi qator yaratish.

        Reklama matni hali kiritilmagan bo'lsa ham interval/davomiylik kabi
        sozlamalarni saqlash imkonini beradi.
        """
        existing = self.get_user_message(telegram_id)
        if existing:
            self.client.table("user_messages").update(fields).eq(
                "id", existing["id"]
            ).execute()
        else:
            data = {"user_telegram_id": telegram_id, **fields}
            self.client.table("user_messages").insert(data).execute()

    def set_message_running(self, telegram_id: int, is_running: bool) -> None:
        """Xabar yuborishni boshlash/to'xtatish."""
        fields: dict[str, Any] = {"is_running": is_running}
        if is_running:
            fields["started_running_at"] = datetime.now(timezone.utc).isoformat()
        self.update_message_settings(telegram_id, **fields)

    def set_last_sent(self, telegram_id: int) -> None:
        """So'nggi yuborilgan vaqtni belgilash."""
        self.update_message_settings(
            telegram_id,
            last_sent_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_running_messages(self) -> list[dict]:
        """Faol (is_running=True) barcha xabarlarni olish."""
        result = (
            self.client.table("user_messages")
            .select("*, users!inner(telegram_id, language, session_string, status, "
                    "trial_messages_left, subscription_end, "
                    "blocked_until, msg_blocked_until)")
            .eq("is_running", True)
            .execute()
        )
        return result.data or []

    def get_running_count(self) -> int:
        """Hozirda faol tarqatishlar (is_running=True) sonini qaytaradi."""
        result = (
            self.client.table("user_messages")
            .select("id")
            .eq("is_running", True)
            .execute()
        )
        return len(result.data or [])

    # ─────────────────────────────────────────────────────────────────────────
    # STATISTICS (Statistika)
    # ─────────────────────────────────────────────────────────────────────────

    def get_stats(self, telegram_id: int) -> Optional[dict]:
        """Foydalanuvchi statistikasini olish."""
        result = (
            self.client.table("statistics")
            .select("*")
            .eq("user_telegram_id", telegram_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def increment_sent(self, telegram_id: int) -> None:
        """Muvaffaqiyatli yuborilgan xabar sonini oshirish."""
        stats = self.get_stats(telegram_id)
        now = datetime.now(timezone.utc).isoformat()
        if stats:
            self.client.table("statistics").update({
                "sent_count": stats["sent_count"] + 1,
                "last_updated": now,
            }).eq("id", stats["id"]).execute()
        else:
            self.client.table("statistics").insert({
                "user_telegram_id": telegram_id,
                "sent_count": 1,
                "failed_count": 0,
                "last_updated": now,
            }).execute()

    def increment_failed(self, telegram_id: int) -> None:
        """Muvaffaqiyatsiz xabar sonini oshirish."""
        stats = self.get_stats(telegram_id)
        now = datetime.now(timezone.utc).isoformat()
        if stats:
            self.client.table("statistics").update({
                "failed_count": stats["failed_count"] + 1,
                "last_updated": now,
            }).eq("id", stats["id"]).execute()
        else:
            self.client.table("statistics").insert({
                "user_telegram_id": telegram_id,
                "sent_count": 0,
                "failed_count": 1,
                "last_updated": now,
            }).execute()

    def get_total_stats(self) -> dict:
        """Umumiy statistikani olish (admin panel uchun)."""
        result = self.client.table("statistics").select("*").execute()
        data = result.data or []
        total_sent = sum(s.get("sent_count", 0) for s in data)
        total_failed = sum(s.get("failed_count", 0) for s in data)
        return {
            "total_sent": total_sent,
            "total_failed": total_failed,
            "total_users": len(data),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # SYSTEM ADMINS (Admin panel foydalanuvchilari)
    # ─────────────────────────────────────────────────────────────────────────

    def get_admin(self, username: str) -> Optional[dict]:
        """Admin ma'lumotlarini olish."""
        result = (
            self.client.table("system_admins")
            .select("*")
            .eq("username", username)
            .execute()
        )
        return result.data[0] if result.data else None

    def create_admin(self, username: str, password_hash: str,
                     role: str = "admin") -> dict:
        """Yangi admin yaratish."""
        data = {
            "username": username,
            "password_hash": password_hash,
            "role": role,
        }
        result = self.client.table("system_admins").insert(data).execute()
        return result.data[0] if result.data else data


# Yagona global instansiya
db = SupabaseDB()
