"""
Matnlar paketi — ikki tildagi (uz_lat, uz_cyr) barcha bot matnlarini boshqaradi.
"""

from app.bot.texts.uz_lat import TEXTS as TEXTS_LAT
from app.bot.texts.uz_cyr import TEXTS as TEXTS_CYR

# Til kodlariga mos lug'atlar
_LANG_MAP: dict[str, dict[str, str]] = {
    "uz_lat": TEXTS_LAT,
    "uz_cyr": TEXTS_CYR,
}


def get_text(key: str, lang: str = "uz_lat") -> str:
    """Berilgan kalit va til bo'yicha matnni qaytaradi.

    Args:
        key:  matn kaliti (masalan, 'welcome', 'btn_stats')
        lang: til kodi — 'uz_lat' yoki 'uz_cyr'

    Returns:
        Topilgan matn yoki kalit nomi (agar matn topilmasa).
    """
    texts = _LANG_MAP.get(lang, TEXTS_LAT)
    return texts.get(key, key)
