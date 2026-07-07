"""
Telegram WebApp marshrutlari.
Guruhlarni boshqarish uchun sahifa va API.
"""

import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

from app.config import BOT_TOKEN, MAX_GROUPS_PER_USER
from app.database.supabase_client import db

router = APIRouter(prefix="/webapp", tags=["webapp"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

class GroupUpdate(BaseModel):
    group_id: str
    is_active: bool

class GroupsUpdateRequest(BaseModel):
    initData: str
    updates: list[GroupUpdate]

def validate_webapp_data(init_data: str) -> dict:
    """Telegram WebApp initData ni tekshirish va ma'lumotlarni ajratib olish."""
    try:
        parsed_data = dict(parse_qsl(init_data))
        if "hash" not in parsed_data:
            raise ValueError("No hash in initData")

        hash_val = parsed_data.pop("hash")
        
        # Alfavit bo'yicha saralash va qatorga keltirish
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash != hash_val:
            raise ValueError("Invalid hash")
            
        user_data = json.loads(parsed_data.get("user", "{}"))
        return user_data
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {e}")

@router.get("/groups", response_class=HTMLResponse)
async def webapp_groups_page(request: Request):
    """Guruhlarni boshqarish WebApp sahifasi."""
    return templates.TemplateResponse("groups.html", {"request": request})

@router.get("/api/groups")
async def get_groups(initData: str):
    """Guruhlar ro'yxatini qaytarish."""
    user_data = validate_webapp_data(initData)
    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="No user id")
        
    groups = db.get_user_groups(telegram_id)
    return {"groups": groups, "max_groups": MAX_GROUPS_PER_USER}

@router.post("/api/groups")
async def update_groups(request_data: GroupsUpdateRequest):
    """Guruhlar holatini yangilash."""
    user_data = validate_webapp_data(request_data.initData)
    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="No user id")
        
    all_groups = db.get_user_groups(telegram_id)
    
    # Kutilayotgan active sonini hisoblash
    current_active_count = sum(1 for g in all_groups if g.get("is_active"))
    
    # Faqat bizga kelgan updateslarni qayta ishlaymiz
    updates_dict = {u.group_id: u.is_active for u in request_data.updates}
    
    # Oldin yangi count ni hisoblaymiz
    new_active_count = 0
    for g in all_groups:
        gid = str(g.get("id"))
        is_active = updates_dict.get(gid, g.get("is_active"))
        if is_active:
            new_active_count += 1
            
    if new_active_count > MAX_GROUPS_PER_USER:
        raise HTTPException(status_code=400, detail=f"Maksimal guruhlar soni {MAX_GROUPS_PER_USER} ta bo'lishi mumkin.")
        
    # Bazada yangilash
    for g in all_groups:
        gid = str(g.get("id"))
        if gid in updates_dict:
            new_state = updates_dict[gid]
            if new_state != g.get("is_active"):
                db.toggle_group(gid, new_state)
                
    return {"success": True}
