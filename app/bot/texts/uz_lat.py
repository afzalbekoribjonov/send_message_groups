"""
O'zbek-Lotin (uz_lat) tilidagi barcha bot matnlari.
"""

TEXTS: dict[str, str] = {
    # ── Boshlang'ich ────────────────────────────────────────────────────────
    "welcome": (
        "👋 Xush kelibsiz, <b>Xabarchi Bot</b>ga!\n\n"
        "Bu bot sizga guruhlaringizga avtomatik reklama xabarlarini "
        "yuborishda yordam beradi.\n\n"
        "Davom etish uchun tilni tanlang 👇"
    ),
    "choose_language": "🌐 Tilni tanlang:",
    "language_changed": "✅ Til muvaffaqiyatli o'zgartirildi!",

    # ── Asosiy menyu ────────────────────────────────────────────────────────
    "main_menu": (
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:"
    ),

    # ── Statistika ──────────────────────────────────────────────────────────
    "stats_title": "📊 <b>Statistika</b>",
    "stats_info": (
        "📊 <b>Statistika</b>\n\n"
        "✅ Yuborilgan: <b>{sent_count}</b>\n"
        "❌ Xatolik: <b>{failed_count}</b>\n"
        "🎁 Sinov qoldi: <b>{trial_left}</b>\n"
        "📡 Holat: <b>{status}</b>"
    ),
    "broadcast_state_running": "🟢 Tarqatish hozir <b>ishlamoqda</b>.",
    "broadcast_state_stopped": "🔴 Tarqatish hozir <b>to'xtatilgan</b>.",
    "stats_refreshed": "🔄 Yangilandi",
    "trial_expired_short": "⏰ Bepul sinov tugadi. Admin bilan bog'laning.",

    # ── Sozlamalar ──────────────────────────────────────────────────────────
    "settings_title": (
        "⚙️ <b>Sozlamalar</b>\n\n"
        "Quyidagi parametrlarni o'zgartiring:"
    ),
    "settings_interval": "⏱ Hozirgi interval: <b>{interval} daqiqa</b>\nYangi intervalni kiriting (daqiqada):",
    "settings_duration": "⏳ Hozirgi davomiylik: <b>{duration} soat</b>\nYangi davomiylikni kiriting (soatda, 0 = cheksiz):",
    "interval_set": "✅ Interval <b>{interval} daqiqa</b>ga o'rnatildi.",
    "duration_set": "✅ Davomiylik <b>{duration} soat</b>ga o'rnatildi.",
    "interval_too_low": "⚠️ Minimal interval — <b>2 daqiqa</b>. Iltimos, kattaroq son kiriting.",
    "enter_number": "⚠️ Iltimos, faqat son kiriting (masalan: <code>5</code>).",

    # ── Yordam ──────────────────────────────────────────────────────────────
    "help_text": (
        "ℹ️ <b>Yordam</b>\n\n"
        "1️⃣ <b>Akkauntni ulash</b> — Telegram hisobingizni ulang\n"
        "2️⃣ <b>Reklama matni</b> — Reklama xabarini yozing\n"
        "3️⃣ <b>Guruhlar</b> — Xabar yuboriladigan guruhlarni tanlang\n"
        "4️⃣ <b>Tarqatishni boshlash</b> — Xabar yuborishni yoqing\n"
        "5️⃣ <b>Sozlamalar</b> — Interval va davomiylikni sozlang\n\n"
        "🎁 <b>Bepul tarif:</b> faqat <b>{trial}</b> ta xabar yubora olasiz.\n"
        "Limitni oshirish (obuna) uchun admin bilan bog'laning 👇\n\n"
        "📞 Telefon: {support_phone}\n"
        "💬 Admin: {support_username}"
    ),

    # ── Akkauntni ulash (Login) ─────────────────────────────────────────────
    "link_account": "🔗 Telegram hisobingizni ulash uchun telefon raqamingizni yuboring.\n\n📱 Format: <code>+998XXXXXXXXX</code>",
    "enter_phone": "📱 Telefon raqamingizni kiriting:\n\nFormat: <code>+998XXXXXXXXX</code>",
    "enter_code": "📨 <b>{digits}</b> xonali tasdiqlash kodi {where} yuborildi.\n\nQuyidagi tugmalar orqali kodni kiriting:\n\n🔢 Kiritilgan: <b>{entered}</b>\n\n💡 Kod kelmasa, pastdagi «🔁 Qayta yuborish» tugmasini bosing.",
    "code_via_app": "<b>Telegram ilovangizga</b> (rasmiy «Telegram» xizmat chatiga — 777000)",
    "code_via_sms": "<b>SMS</b> orqali telefoningizga",
    "code_via_call": "<b>telefon qo'ng'irog'i</b> orqali (avtomatik ovoz kodni o'qiydi)",
    "code_via_flash_call": "<b>qo'ng'iroq</b> orqali",
    "code_via_missed_call": "<b>javobsiz qo'ng'iroq</b> orqali (qo'ng'iroq qilgan raqamning oxirgi raqamlari — bu kod)",
    "code_via_fragment": "<b>Fragment</b> (fragment.com hisobingizga)",
    "code_via_email": "<b>email</b> orqali",
    "code_resent": "🔁 Kod boshqa kanal orqali qayta yuborildi.",
    "code_resent_alert": "Kod qayta yuborildi ✅",
    "err_api_invalid": "❌ API_ID yoki API_HASH noto'g'ri. Admin <code>.env</code> faylini tekshirishi kerak.",
    "err_phone_invalid": "❌ Telefon raqami noto'g'ri. To'g'ri formatda qayta kiriting: <code>+998XXXXXXXXX</code>",
    "err_phone_banned": "🚫 Bu telefon raqami Telegram tomonidan bloklangan.",
    "err_phone_flood": "⏳ Juda ko'p urinish bo'ldi. Iltimos, birozdan so'ng qayta urinib ko'ring.",
    "err_flood_wait": "⏳ Juda ko'p so'rov yuborildi. <b>{seconds}</b> soniyadan keyin qayta urinib ko'ring.",
    "code_hint": "💡 Kodni raqamli tugmalar yordamida kiriting.",
    "code_entered": "🔢 Kiritilgan: <b>{entered}</b>",
    "code_wrong": "❌ Kod noto'g'ri! Qayta urinib ko'ring.",
    "enter_2fa": "🔐 Ikki bosqichli parolni kiriting:",
    "login_success": "✅ Hisob muvaffaqiyatli ulandi! Endi botdan to'liq foydalanishingiz mumkin.",
    "login_failed": "❌ Tizimga kirish amalga oshmadi: <code>{error}</code>",
    "already_linked": (
        "✅ Hisobingiz allaqachon ulangan!\n\n"
        "Boshqa hisob ulamoqchi bo'lsangiz, avval "
        "⚙️ Sozlamalar → 🚪 Hisobdan chiqish ni bosing."
    ),
    "no_account": "⚠️ Avval hisobingizni ulang: «🔗 Akkauntni ulash» tugmasini bosing.",

    # ── Reklama matni ───────────────────────────────────────────────────────
    "enter_ad_text": "📝 Yangi reklama matnini yozing va yuboring:",
    "ad_text_saved": "✅ Reklama matni saqlandi!",
    "no_ad_text": "⚠️ Hali reklama matni kiritilmagan. Matn yozing va yuboring.",
    "current_ad": "📄 Hozirgi reklama matni:\n\n{text}\n\nYangi matn yuborish uchun shunchaki yozing 👇",

    # ── Guruhlar ────────────────────────────────────────────────────────────
    "groups_loading": "⏳ Guruhlar yuklanmoqda...",
    "groups_list": "📋 <b>Guruhlaringiz</b>\n\nGuruhni yoqish/o'chirish uchun bosing:",
    "group_selected": "✅ <b>{title}</b> — yoqildi",
    "group_deselected": "❌ <b>{title}</b> — o'chirildi",
    "no_groups": "😕 Siz hech qanday guruhda a'zo emassiz yoki guruhlar topilmadi.",
    "max_groups_reached": "⚠️ Maksimal guruhlar soniga yetdingiz ({max}).",

    # ── Tarqatish (Broadcast) ───────────────────────────────────────────────
    "broadcast_started": "🚀 Xabar tarqatish boshlandi!",
    "broadcast_stopped": "🛑 Xabar tarqatish to'xtatildi.",
    "broadcast_already_running": "⚠️ Tarqatish allaqachon ishlayapti!",
    "broadcast_not_running": "⚠️ Tarqatish hozir ishlamayapti.",
    "no_groups_selected": "⚠️ Guruhlar tanlanmagan! Avval guruhlarni tanlang.",
    "no_message_set": "⚠️ Reklama matni kiritilmagan! Avval matn yozing.",

    # ── Obuna / Trial ──────────────────────────────────────────────────────
    "trial_expired": (
        "⏰ Bepul sinov muddati tugadi!\n\n"
        "Davom etish uchun obunani faollashtiring.\n"
        "📞 Bog'lanish: {support_phone}\n"
        "💬 Admin: {support_username}"
    ),
    "subscription_info": (
        "💎 <b>Obuna ma'lumotlari</b>\n\n"
        "Obuna tugash sanasi: <b>{end_date}</b>\n"
        "Holat: <b>{status}</b>"
    ),

    # ── Avtomatik ogohlantirishlar (scheduler yuboradi) ──────────────────────
    "notify_trial_expired": (
        "⏰ <b>Bepul sinov tugadi!</b>\n\n"
        "Sinov xabarlaringiz tugagani uchun tarqatish <b>avtomatik to'xtatildi</b>.\n\n"
        "Cheksiz xabar yuborish uchun obuna oling 👇\n"
        "📞 {support_phone}\n"
        "💬 {support_username}"
    ),
    "notify_subscription_expired": (
        "⏰ <b>Obunangiz muddati tugadi!</b>\n\n"
        "Shu sababli tarqatish <b>avtomatik to'xtatildi</b>.\n\n"
        "Obunani yangilash uchun 👇\n"
        "📞 {support_phone}\n"
        "💬 {support_username}"
    ),
    "notify_trial_low": (
        "⚠️ <b>Diqqat!</b> Bepul sinovdan atigi <b>{left}</b> ta xabar qoldi.\n\n"
        "Uzluksiz ishlash uchun obuna olishni o'ylab ko'ring: {support_username}"
    ),
    "notify_blocked": (
        "🚫 <b>Hisobingiz bloklandi.</b>\n\n"
        "Tarqatish to'xtatildi. Ma'lumot uchun: {support_username}"
    ),
    "notify_duration_done": (
        "✅ Belgilangan vaqt (<b>{hours} soat</b>) tugadi.\n"
        "Tarqatish avtomatik to'xtatildi. Qaytadan boshlashingiz mumkin."
    ),
    "notify_stopped": "🛑 Tarqatish to'xtatildi.",

    # ── Tarif holati (statistikada ko'rsatiladi) ─────────────────────────────
    "plan_subscribed": "💎 <b>Tarif:</b> Obuna faol ({date} gacha) — cheksiz xabar",
    "plan_trial": "🎁 <b>Tarif:</b> Bepul sinov — <b>{left}</b> ta xabar qoldi",
    "plan_expired": "⛔ <b>Tarif:</b> Bepul sinov tugagan. Obuna oling.",

    # ── Xatolik ─────────────────────────────────────────────────────────────
    "error_generic": "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",

    # ── Tugma matnlari ──────────────────────────────────────────────────────
    "btn_stats": "📊 Statistika",
    "btn_settings": "⚙️ Sozlamalar",
    "btn_ad_text": "📝 Reklama matni",
    "btn_groups": "📋 Guruhlar",
    "btn_start_broadcast": "🚀 Tarqatishni boshlash",
    "btn_stop_broadcast": "🛑 Tarqatishni to'xtatish",
    "btn_help": "ℹ️ Yordam",
    "btn_link_account": "🔗 Akkauntni ulash",
    "btn_back": "⬅️ Ortga",
    "btn_lang_lat": "🇺🇿 O'zbekcha (Lotin)",
    "btn_lang_cyr": "🇺🇿 Ўзбекча (Кирилл)",
    "btn_interval": "⏱ Interval",
    "btn_duration": "⏳ Davomiylik",
    "btn_logout": "🚪 Hisobdan chiqish",
    "btn_stats_stop": "🛑 To'xtatish",
    "btn_stats_start": "🚀 Boshlash",
    "btn_stats_refresh": "🔄 Yangilash",
    "btn_stats_close": "❌ Yopish",
    "btn_resend_code": "🔁 Kod kelmadimi? Qayta yuborish",
    "logout_confirm": "⚠️ Rostdan ham hisobingizdan chiqmoqchimisiz?\n\nUlangan akkaunt o'chiriladi va tarqatish to'xtaydi. Qaytadan ulashingiz mumkin.",
    "logout_cancelled": "✅ Bekor qilindi. Hisobingiz ulangan holicha qoldi.",
    "logout_success": "🚪 Hisobingiz muvaffaqiyatli o'chirildi (tizimdan chiqildi).",
    "btn_yes": "✅ Ha",
    "btn_no": "❌ Yo'q",
}
