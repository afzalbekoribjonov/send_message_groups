"""
Loyiha asosiy kirish nuqtasi.
FastAPI ilovasi, Telegram Bot va APScheduler'ni bitta jarayonda ishga tushiradi.
"""


import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import DEBUG, PORT, ADMIN_USERNAME, ADMIN_PASSWORD
from app.database.supabase_client import db
from app.admin.auth import hash_password
from app.admin.routes import router as admin_router
from app.webapp.routes import router as webapp_router
from app.bot.bot import start_bot
from app.scheduler.jobs import setup_scheduler

# Log sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Scheduler obyekti
scheduler = None


async def seed_admin():
    """Birlamchi admin foydalanuvchisini bazada yaratish (agar mavjud bo'lsa)."""
    try:
        admin = db.get_admin(ADMIN_USERNAME)
        if not admin:
            hashed = hash_password(ADMIN_PASSWORD)
            db.create_admin(ADMIN_USERNAME, hashed, "super_admin")
            logger.info("Birlamchi admin muvaffaqiyatli yaratildi: %s", ADMIN_USERNAME)
        else:
            logger.info("Admin foydalanuvchi allaqachon mavjud.")
    except Exception as e:
        logger.error("Admin seed qilishda xato: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info("🚀 Tizim ishga tushmoqda...")
    
    # 1. Admin tekshirish va yaratish
    await seed_admin()
    
    # 2. Telegram Botni backgroundda ishga tushirish
    bot_task = asyncio.create_task(start_bot())
    logger.info("🤖 Telegram Bot background task'da ishga tushirildi.")
    
    # 3. APSchedulerni sozlash va ishga tushirish
    global scheduler
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("⏱ APScheduler ishga tushirildi.")
    
    yield
    
    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("🛑 Tizim to'xtatilmoqda...")
    
    # 1. Schedulerni to'xtatish
    if scheduler:
        scheduler.shutdown()
        logger.info("⏱ APScheduler to'xtatildi.")
        
    # 2. Telegram Bot taskini bekor qilish
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        logger.info("🤖 Telegram Bot taski bekor qilindi.")
    except Exception as e:
        logger.error("Telegram Bot to'xtashida xato: %s", e)


# FastAPI ilovasi
app = FastAPI(
    title="Xabarchi Bot",
    description="Taksi foydalanuvchilari uchun reklama tarqatuvchi tizim",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,       # Admin xavfsizligi uchun API docs o'chirilgan
    redoc_url=None,
)

# Statik fayllarni ulash (WebApp CSS/JS uchun)
import os
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "webapp", "static")), name="static")

# Yo'nalishlarni ulash
app.include_router(admin_router)
app.include_router(webapp_router)


@app.get("/")
async def root():
    """Asosiy sahifadan admin panel dashboard'ga yo'naltirish."""
    return RedirectResponse(url="/admin/dashboard")


@app.api_route("/ping", methods=["GET", "HEAD"])
async def ping():
    """Keep-Alive (ping) endpoint - Render serverini uyg'oq saqlash uchun.

    GET va HEAD so'rovlarini ham qabul qiladi va 200 qaytaradi
    (UptimeRobot/Cron-Job HEAD so'rovlari uchun).
    """
    return {"status": "ok", "message": "pong"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Uvicorn ishga tushmoqda, port: %d", PORT)
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=DEBUG)
