"""
Admin panel autentifikatsiyasi.
JWT token asosidagi cookie-based sessiya boshqaruvi.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import ADMIN_SECRET_KEY

logger = logging.getLogger(__name__)

# ── Parol hashing ────────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── JWT sozlamalari ──────────────────────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
COOKIE_NAME = "admin_token"


def hash_password(password: str) -> str:
    """Parolni bcrypt bilan hashlash."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Parolni tekshirish."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT access token yaratish.

    Args:
        data: Token payload (masalan, {"sub": "admin"}).
        expires_delta: Muddati (default: 24 soat).

    Returns:
        Imzolangan JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, ADMIN_SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """
    JWT tokenni tekshirish va payload qaytarish.

    Returns:
        Token payload yoki None (agar noto'g'ri bo'lsa).
    """
    try:
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_admin(request: Request) -> Optional[dict]:
    """
    FastAPI dependency – cookie'dan admin ma'lumotlarini olish.

    Args:
        request: FastAPI Request obyekti.

    Returns:
        Admin ma'lumotlari dict yoki None.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None

    payload = verify_token(token)
    if payload is None:
        return None

    username = payload.get("sub")
    if not username:
        return None

    return {"username": username, "role": payload.get("role", "admin")}
