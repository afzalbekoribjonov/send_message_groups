# Xabarchi Bot — Taksi Foydalanuvchilari Uchun Avtomatik Reklama Yuborish Tizimi

Ushbu tizim taksi haydovchilari/foydalanuvchilari uchun mo'ljallangan bo'lib, o'z Telegram akkaunti (Userbot) orqali turli guruhlarga avtomatik va belgilangan vaqt oralig'ida (interval) reklama xabarlarini yuborishni ta'minlaydi. 

Tizim FastAPI veb-boshqaruv paneli (Admin Panel) va aiogram v3 kutubxonasida yaratilgan boshqaruv Telegram boti, Pyrogram (Userbot) va Supabase (bulutli PostgreSQL) bazasidan iborat.

---

## 🛠 Texnologiyalar (Tech Stack)

* **Python 3.11 / 3.12**
* **FastAPI** + **Jinja2 Templates** (Admin Panel boshqaruvi)
* **aiogram v3.x** (Boshqaruv Telegram boti)
* **Pyrogram v2.0+** (Guruhlarga xabar yuborish userboti)
* **Supabase (PostgreSQL)** (Ma'lumotlar bazasi va session saqlash)
* **APScheduler** (Rejalashtirilgan ishlar va intervalli jo'natish)
* **Docker** (Konteynerizatsiya va oson deploy)

---

## 📂 Supabase Ma'lumotlar Bazasi Tuzilishi (SQL)

Supabase boshqaruv panelining **SQL Editor** bo'limiga kirib, quyidagi so'rovlarni ishga tushiring:

```sql
-- 1. Foydalanuvchilar (Taksilar va Adminlar) jadvali
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(100),
    first_name VARCHAR(100),
    phone_number VARCHAR(20),
    language VARCHAR(5) DEFAULT 'uz_lat', -- uz_lat, uz_cyr
    session_string TEXT, -- Pyrogram String Session
    status VARCHAR(30) DEFAULT 'new', -- new, pending_code, pending_2fa, active, blocked
    trial_messages_left INT DEFAULT 15, -- Bepul sinov xabarlari
    subscription_end TIMESTAMP WITH TIME ZONE NULL, -- Obuna tugash vaqti
    blocked_until TIMESTAMP WITH TIME ZONE NULL,
    msg_blocked_until TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Taksilarning guruhlari jadvali
CREATE TABLE user_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    chat_id BIGINT NOT NULL,
    group_title VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Taksilarning reklama xabarlari va ularning sozlamalari
CREATE TABLE user_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    message_text TEXT,
    interval_minutes INT DEFAULT 2, -- Minimal 2 daqiqa
    is_running BOOLEAN DEFAULT FALSE,
    duration_hours INT DEFAULT 0, -- 0 bo'lsa cheksiz
    started_running_at TIMESTAMP WITH TIME ZONE NULL,
    last_sent_at TIMESTAMP WITH TIME ZONE NULL
);

-- 4. Tizim xavfsizligi va xabarlar statistikasi
CREATE TABLE statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    sent_count INT DEFAULT 0,
    failed_count INT DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Admin hisoblari (Veb panelga kirish uchun)
CREATE TABLE system_admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'admin',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚙️ Sozlash (Configuration)

Loyiha ildiz papkasida `.env` faylini yarating va unga quyidagi o'zgaruvchilarni kiriting:

```env
# Telegram Bot Token
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Telegram API sozlamalari (my.telegram.org saytidan olinadi)
API_ID=12345678
API_HASH=abcdef0123456789abcdef0123456789

# Supabase URL va Anon Key
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Admin Panel sozlamalari
ADMIN_SECRET_KEY=i_am_a_very_secret_key_at_least_32_characters_long
ADMIN_USERNAME=admin
ADMIN_PASSWORD=strong_admin_password_here

# Server sozlamalari
PORT=8000
DEBUG=false
```

---

## 🚀 Ishga Tushirish (Lokal/Docker)

### Python Virtual Environment orqali:

1. Kutubxonalarni o'rnatish:
   ```bash
   pip install -r requirements.txt
   ```

2. Ilovani ishga tushirish:
   ```bash
   python -m app.main
   ```

### Docker orqali:

1. Docker konteynerini yig'ish va ishga tushirish:
   ```bash
   docker-compose up --build -d
   ```

Tizim ishga tushgach, admin panelga quyidagi manzil orqali kirish mumkin:
* **Admin Panel:** [http://localhost:8000/admin/login](http://localhost:8000/admin/login)
* **Keep-Alive (Ping) URL:** [http://localhost:8000/ping](http://localhost:8000/ping)

---

## ☁️ Render.com Deployment (Keep-Alive)

Render.com loyihalari bepul (Free) tarifida 15 daqiqa HTTP so'rovlar kelmasa uyqu rejimiga o'tadi va barcha foniy jarayonlarni (Telegram bot va Scheduler ishlarini) to'xtatadi.

Buning oldini olish uchun:
1. Loyihani Render.com da **Web Service** sifatida yuklang.
2. Atrof-muhit o'zgaruvchilarini (Environment Variables) sozlang.
3. Loyiha muvaffaqiyatli yuklangandan so'ng, [Cron-Job.org](https://cron-job.org/) yoki [UptimeRobot](https://uptimerobot.com/) xizmatlaridan ro'yxatdan o'ting.
4. Render loyihangizning `/ping` endpointiga (masalan: `https://your-app.onrender.com/ping`) har **10 daqiqada** HTTP so'rov (ping) yuborib turuvchi cron-job sozlang.
5. Bu tizim Render serveringizni 24/7 faol holatda saqlaydi!

---

## 🛡 Admin Panel — To'liq Nazorat Paneli

Admin panel (`/admin`) har bir taksi foydalanuvchisini to'liq boshqarish imkonini beradi:

* **Dashboard** — jami/faol/bloklangan foydalanuvchilar, faol tarqatishlar soni, yuborilgan va xato xabarlar statistikasi.
* **Foydalanuvchi kartasi** quyidagilarni boshqaradi:
  * **Holat:** to'liq bloklash / blokdan chiqarish.
  * **Vaqtinchalik blok:** belgilangan soatga (avtomatik tugaydi).
  * **Obuna:** kunlab uzaytirish (mavjud obuna ustiga qo'shiladi) yoki bekor qilish.
  * **Reklama bloki:** xabar yuborishni soatlab cheklash yoki cheklovni olib tashlash.
  * **Bepul sinov:** sinov xabarlari sonini o'zgartirish.
  * **Tarqatish:** majburan boshlash / to'xtatish.
  * **Reklama matni va sozlamalari:** matn, interval (min. 2 daqiqa) va davomiylikni tahrirlash.
  * **Guruhlar:** har bir guruhni yoqish/o'chirish yoki butunlay o'chirish.
  * **Foydalanuvchini o'chirish** (barcha bog'liq ma'lumotlari bilan, tasdiq so'raladi).

Barcha amallardan so'ng natija haqida flash-xabar ko'rsatiladi; xavfli amallar tasdiqlashni talab qiladi.

---

## 🌐 Til Tanlash Mantig'i

* Til **faqat birinchi marta** `/start` bosilganda so'raladi (yangi foydalanuvchida `language = NULL`).
* Til tanlangach, keyingi `/start` lar to'g'ridan-to'g'ri asosiy menyuni ochadi.
* Tilni keyinchalik **⚙️ Sozlamalar** menyusidan istalgan vaqtda almashtirish mumkin.

> Eslatma: Ma'lumotlar bazasi sxemasi o'zgarmaydi — `users.language` ustuni `NULL` qabul qiladi (til hali tanlanmaganligini bildiradi).
