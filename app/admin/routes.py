"""
Admin panel marshrutlari (routes).

Dashboard, foydalanuvchilar ro'yxati, foydalanuvchi tafsilotlari, login/logout
va to'liq boshqaruv amallari (bloklash, obuna, trial, reklama, guruhlar,
tarqatish, o'chirish).
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import (
    ADMIN_USERNAME, ADMIN_PASSWORD, MIN_INTERVAL_MINUTES, FREE_TRIAL_MESSAGES,
)
from app.database.supabase_client import db
from app.admin.auth import (
    verify_password,
    create_access_token,
    get_current_admin,
    COOKIE_NAME,
)

logger = logging.getLogger(__name__)

# ── Router va Templates ─────────────────────────────────────────────────────
router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(
    directory=str(Path(__file__).parent / "templates")
)


# ── Yordamchi funksiyalar ────────────────────────────────────────────────────

def _require_admin(admin: Optional[dict]) -> Optional[RedirectResponse]:
    """Admin autentifikatsiyasini tekshirish. None qaytarsa — admin mavjud."""
    if admin is None:
        return RedirectResponse(url="/admin/login", status_code=302)
    return None


def _flash_redirect(telegram_id: int, msg: str, ftype: str = "success") -> RedirectResponse:
    """Foydalanuvchi sahifasiga flash xabar bilan qaytarish."""
    url = f"/admin/users/{telegram_id}?flash={quote(msg)}&ftype={ftype}"
    return RedirectResponse(url=url, status_code=302)


# ═════════════════════════════════════════════════════════════════════════════
# LOGIN / LOGOUT
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login sahifasini ko'rsatish."""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None,
    })


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Login so'rovini qayta ishlash."""
    authenticated = False
    role = "admin"

    # Konfiguratsiya orqali tekshirish (sodda rejim)
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        authenticated = True
        role = "super_admin"
    else:
        # Supabase'dan tekshirish (kengaytirilgan rejim)
        try:
            admin_data = db.get_admin(username)
            if admin_data and verify_password(password, admin_data.get("password_hash", "")):
                authenticated = True
                role = admin_data.get("role", "admin")
        except Exception as e:
            logger.error("Admin tekshirishda xato: %s", e)

    if authenticated:
        token = create_access_token({"sub": username, "role": role})
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            max_age=86400,  # 24 soat
            samesite="lax",
        )
        logger.info("Admin tizimga kirdi: %s", username)
        return response

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Noto'g'ri login yoki parol!",
    })


@router.get("/logout")
async def logout():
    """Admin tizimdan chiqishi."""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


# ═════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Bosh sahifa – statistika va umumiy ko'rinish."""
    admin = await get_current_admin(request)
    redirect = _require_admin(admin)
    if redirect:
        return redirect

    all_users = db.get_all_users()
    active_users = [u for u in all_users if u.get("status") == "active"]
    blocked_users = [u for u in all_users if u.get("status") == "blocked"]
    total_stats = db.get_total_stats()
    try:
        running_count = db.get_running_count()
    except Exception:
        running_count = 0

    recent_users = all_users[:10]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "admin": admin,
        "total_users": len(all_users),
        "active_users": len(active_users),
        "blocked_users": len(blocked_users),
        "running_count": running_count,
        "total_sent": total_stats.get("total_sent", 0),
        "total_failed": total_stats.get("total_failed", 0),
        "recent_users": recent_users,
    })


# ═════════════════════════════════════════════════════════════════════════════
# USERS (Foydalanuvchilar)
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/users", response_class=HTMLResponse)
async def users_list(request: Request):
    """Foydalanuvchilar ro'yxati."""
    admin = await get_current_admin(request)
    redirect = _require_admin(admin)
    if redirect:
        return redirect

    users = db.get_all_users()
    return templates.TemplateResponse("users.html", {
        "request": request,
        "admin": admin,
        "users": users,
        "flash": request.query_params.get("flash"),
        "ftype": request.query_params.get("ftype", "success"),
    })


@router.get("/users/{telegram_id}", response_class=HTMLResponse)
async def user_detail(request: Request, telegram_id: int):
    """Foydalanuvchi tafsilotlari sahifasi."""
    admin = await get_current_admin(request)
    redirect = _require_admin(admin)
    if redirect:
        return redirect

    user = db.get_user(telegram_id)
    if not user:
        return RedirectResponse(url="/admin/users", status_code=302)

    groups = db.get_user_groups(telegram_id)
    message = db.get_user_message(telegram_id)
    stats = db.get_stats(telegram_id)
    active_groups = [g for g in groups if g.get("is_active")]

    return templates.TemplateResponse("user_detail.html", {
        "request": request,
        "admin": admin,
        "user": user,
        "groups": groups,
        "active_group_count": len(active_groups),
        "message": message,
        "stats": stats,
        "flash": request.query_params.get("flash"),
        "ftype": request.query_params.get("ftype", "success"),
        "min_interval": MIN_INTERVAL_MINUTES,
        "free_trial": FREE_TRIAL_MESSAGES,
    })


# ═════════════════════════════════════════════════════════════════════════════
# USER ACTIONS — HOLAT / BLOK
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/users/{telegram_id}/block")
async def block_user(request: Request, telegram_id: int):
    """Foydalanuvchini butunlay bloklash."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    db.block_user(telegram_id)
    logger.info("Bloklandi: %s (admin: %s)", telegram_id, admin["username"])
    return _flash_redirect(telegram_id, "Foydalanuvchi bloklandi.", "danger")


@router.post("/users/{telegram_id}/unblock")
async def unblock_user(request: Request, telegram_id: int):
    """Foydalanuvchini blokdan chiqarish (barcha cheklovlarni tozalaydi)."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    db.unblock_user(telegram_id)
    logger.info("Blokdan chiqarildi: %s (admin: %s)", telegram_id, admin["username"])
    return _flash_redirect(telegram_id, "Foydalanuvchi blokdan chiqarildi.")


@router.post("/users/{telegram_id}/temp-block")
async def temp_block_user(request: Request, telegram_id: int, hours: int = Form(...)):
    """Foydalanuvchini vaqtinchalik bloklash (soatlarda)."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    if hours < 1:
        return _flash_redirect(telegram_id, "Soat 1 dan kichik bo'lishi mumkin emas.", "danger")
    until = datetime.now(timezone.utc) + timedelta(hours=hours)
    db.temp_block_user(telegram_id, until)
    logger.info("Vaqtinchalik bloklandi: %s, %dh (admin: %s)", telegram_id, hours, admin["username"])
    return _flash_redirect(telegram_id, f"{hours} soatga vaqtinchalik bloklandi.", "warning")


# ═════════════════════════════════════════════════════════════════════════════
# USER ACTIONS — OBUNA
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/users/{telegram_id}/subscription")
async def set_subscription(request: Request, telegram_id: int, days: int = Form(...)):
    """Obuna muddatini uzaytirish (kunlarda)."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    if days < 1:
        return _flash_redirect(telegram_id, "Kun soni 1 dan kichik bo'lishi mumkin emas.", "danger")
    new_end = db.extend_subscription(telegram_id, days)
    logger.info("Obuna uzaytirildi: %s, +%dd (admin: %s)", telegram_id, days, admin["username"])
    return _flash_redirect(
        telegram_id,
        f"Obuna {days} kunga uzaytirildi ({new_end.strftime('%Y-%m-%d')} gacha).",
    )


@router.post("/users/{telegram_id}/subscription/remove")
async def remove_subscription(request: Request, telegram_id: int):
    """Obunani bekor qilish."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    db.remove_subscription(telegram_id)
    logger.info("Obuna bekor qilindi: %s (admin: %s)", telegram_id, admin["username"])
    return _flash_redirect(telegram_id, "Obuna bekor qilindi.", "warning")


# ═════════════════════════════════════════════════════════════════════════════
# USER ACTIONS — XABAR BLOKI / TRIAL
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/users/{telegram_id}/msg-block")
async def message_block(request: Request, telegram_id: int, hours: int = Form(...)):
    """Xabar yuborishni vaqtinchalik bloklash (soatlarda)."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    if hours < 1:
        return _flash_redirect(telegram_id, "Soat 1 dan kichik bo'lishi mumkin emas.", "danger")
    until = datetime.now(timezone.utc) + timedelta(hours=hours)
    db.block_user_messages(telegram_id, until)
    logger.info("Xabar bloklandi: %s, %dh (admin: %s)", telegram_id, hours, admin["username"])
    return _flash_redirect(telegram_id, f"Reklama yuborish {hours} soatga cheklandi.", "warning")


@router.post("/users/{telegram_id}/msg-unblock")
async def message_unblock(request: Request, telegram_id: int):
    """Xabar yuborish cheklovini olib tashlash."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    db.unblock_user_messages(telegram_id)
    logger.info("Xabar bloki olindi: %s (admin: %s)", telegram_id, admin["username"])
    return _flash_redirect(telegram_id, "Reklama cheklovi olib tashlandi.")


@router.post("/users/{telegram_id}/trial")
async def set_trial(request: Request, telegram_id: int, count: int = Form(...)):
    """Bepul sinov xabarlari sonini belgilash."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    if count < 0:
        return _flash_redirect(telegram_id, "Manfiy son kiritib bo'lmaydi.", "danger")
    db.set_trial(telegram_id, count)
    logger.info("Trial belgilandi: %s = %d (admin: %s)", telegram_id, count, admin["username"])
    return _flash_redirect(telegram_id, f"Sinov xabarlari soni {count} ga o'rnatildi.")


# ═════════════════════════════════════════════════════════════════════════════
# USER ACTIONS — TARQATISH (BROADCAST)
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/users/{telegram_id}/broadcast/start")
async def broadcast_start(request: Request, telegram_id: int):
    """Foydalanuvchi tarqatishini majburan boshlash."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r

    msg = db.get_user_message(telegram_id)
    if not msg or not msg.get("message_text"):
        return _flash_redirect(telegram_id, "Avval reklama matni kiritilishi kerak.", "danger")
    if not db.get_active_groups(telegram_id):
        return _flash_redirect(telegram_id, "Faol guruh tanlanmagan.", "danger")

    db.set_message_running(telegram_id, True)
    logger.info("Tarqatish boshlandi (admin): %s (admin: %s)", telegram_id, admin["username"])
    return _flash_redirect(telegram_id, "Tarqatish boshlandi.")


@router.post("/users/{telegram_id}/broadcast/stop")
async def broadcast_stop(request: Request, telegram_id: int):
    """Foydalanuvchi tarqatishini to'xtatish."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    db.set_message_running(telegram_id, False)
    logger.info("Tarqatish to'xtatildi (admin): %s (admin: %s)", telegram_id, admin["username"])
    return _flash_redirect(telegram_id, "Tarqatish to'xtatildi.", "warning")


# ═════════════════════════════════════════════════════════════════════════════
# USER ACTIONS — REKLAMA MATNI VA SOZLAMALAR
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/users/{telegram_id}/message")
async def edit_message(
    request: Request,
    telegram_id: int,
    message_text: str = Form(""),
    interval_minutes: int = Form(MIN_INTERVAL_MINUTES),
    duration_hours: int = Form(0),
):
    """Reklama matni, interval va davomiylikni tahrirlash."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r

    interval = max(MIN_INTERVAL_MINUTES, interval_minutes)
    duration = max(0, duration_hours)
    db.set_user_message(
        telegram_id,
        message_text.strip(),
        interval_minutes=interval,
        duration_hours=duration,
    )
    logger.info("Reklama tahrirlandi (admin): %s (admin: %s)", telegram_id, admin["username"])
    return _flash_redirect(telegram_id, "Reklama sozlamalari saqlandi.")


# ═════════════════════════════════════════════════════════════════════════════
# USER ACTIONS — GURUHLAR
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/users/{telegram_id}/groups/{group_id}/toggle")
async def toggle_group(request: Request, telegram_id: int, group_id: str):
    """Guruhni faollashtirish/o'chirish."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r

    groups = db.get_user_groups(telegram_id)
    target = next((g for g in groups if str(g.get("id")) == group_id), None)
    if not target:
        return _flash_redirect(telegram_id, "Guruh topilmadi.", "danger")
    db.toggle_group(group_id, not target.get("is_active", False))
    return _flash_redirect(telegram_id, "Guruh holati o'zgartirildi.")


@router.post("/users/{telegram_id}/groups/{group_id}/delete")
async def delete_group(request: Request, telegram_id: int, group_id: str):
    """Guruhni o'chirish."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    db.remove_user_group(group_id)
    return _flash_redirect(telegram_id, "Guruh o'chirildi.", "warning")


# ═════════════════════════════════════════════════════════════════════════════
# USER ACTIONS — FOYDALANUVCHINI O'CHIRISH
# ═════════════════════════════════════════════════════════════════════════════

@router.post("/users/{telegram_id}/delete")
async def delete_user(request: Request, telegram_id: int):
    """Foydalanuvchini va barcha ma'lumotlarini o'chirish."""
    admin = await get_current_admin(request)
    if (r := _require_admin(admin)):
        return r
    db.delete_user(telegram_id)
    logger.info("Foydalanuvchi o'chirildi: %s (admin: %s)", telegram_id, admin["username"])
    msg = quote("Foydalanuvchi o'chirildi.")
    return RedirectResponse(
        url=f"/admin/users?flash={msg}&ftype=warning",
        status_code=302,
    )
