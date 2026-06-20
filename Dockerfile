# ── BUILD STAGE ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Ishchi papkani sozlash
WORKDIR /app

# Atrof-muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tizim paketlarini yangilash va TgCrypto build qilish uchun kerakli asboblarni o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt ni ko'chirish va paketlarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha kodlarini ko'chirish
COPY . .

# Render.com bepul tarifi yoki boshqa muhitda portni sozlash uchun shell bilan ishga tushiramiz
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
