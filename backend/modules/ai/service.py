"""
AI moduli xizmati.

Bu modul:
1. Foydalanuvchi promptini AI provayderiga yuboradi (8-bosqichda).
2. AI javobini qabul qiladi.
3. Javobni AIResponse formatida qaytaradi.

Hozircha (3-bosqich): demo rejim — hardcoded namuna qaytaradi.
"""

import logging

from backend.config import settings
from backend.modules.ai.schemas import AIRequest, AIResponse


logger = logging.getLogger(__name__)


# ============================================
# DEMO NAMUNALAR
# ============================================
# Prompt ichida kalit so'z bo'lsa, mos namunani qaytaramiz
DEMO_TEMPLATES: dict[str, dict] = {
    "talaba": {
        "title": "Talabalar natijalari",
        "columns": ["Ism", "Familiya", "Fan", "Ball", "Natija"],
        "rows": [
            ["Ali", "Karimov", "Python", 92, "O'tdi"],
            ["Malika", "Azizova", "Python", 85, "O'tdi"],
            ["Sardor", "Toshmatov", "Python", 78, "O'tdi"],
            ["Nilufar", "Rahimova", "Python", 65, "O'tdi"],
            ["Jasur", "Usmonov", "Python", 45, "Yiqildi"],
            ["Zulfiya", "Abdullayeva", "Python", 88, "O'tdi"],
            ["Bobur", "Saidov", "Python", 72, "O'tdi"],
            ["Dilnoza", "Yusupova", "Python", 95, "O'tdi"],
            ["Farrux", "Nazarov", "Python", 58, "Yiqildi"],
            ["Kamola", "Ergasheva", "Python", 81, "O'tdi"],
        ],
    },
    "xodim": {
        "title": "Xodimlar ro'yxati",
        "columns": ["ID", "Ism", "Lavozim", "Bo'lim", "Maosh"],
        "rows": [
            [1, "Ali Karimov", "Dasturchi", "IT", 5000],
            [2, "Malika Azizova", "Dizayner", "IT", 4500],
            [3, "Sardor Toshmatov", "Menejer", "Sales", 6000],
            [4, "Nilufar Rahimova", "Hisobchi", "Finance", 4000],
            [5, "Jasur Usmonov", "Dasturchi", "IT", 5500],
        ],
    },
    "mahsulot": {
        "title": "Mahsulotlar ro'yxati",
        "columns": ["ID", "Nomi", "Kategoriya", "Narx", "Miqdor"],
        "rows": [
            [1, "Noutbuk", "Elektronika", 1200, 15],
            [2, "Telefon", "Elektronika", 800, 30],
            [3, "Kitob", "Ta'lim", 25, 100],
            [4, "Qalam", "Ofis", 2, 500],
            [5, "Stol", "Mebel", 150, 20],
        ],
    },
    "loyiha": {
        "title": "Loyihalar jadvali",
        "columns": ["Loyiha", "Mas'ul", "Boshlanish", "Tugash", "Holat"],
        "rows": [
            ["Sayt", "Ali Karimov", "2024-01-01", "2024-03-01", "Tugallandi"],
            ["Mobil ilova", "Malika Azizova", "2024-02-15", "2024-06-30", "Davom etmoqda"],
            ["CRM", "Sardor Toshmatov", "2024-03-01", "2024-08-01", "Rejalashtirilgan"],
        ],
    },
}

# Standart namuna — prompt mos kelmasa
DEFAULT_DEMO = {
    "title": "Namunaviy jadval",
    "columns": ["№", "Nomi", "Tavsif", "Holat"],
    "rows": [
        [1, "Element 1", "Tavsif 1", "Faol"],
        [2, "Element 2", "Tavsif 2", "Nofaol"],
        [3, "Element 3", "Tavsif 3", "Faol"],
    ],
}


# ============================================
# ASOSIY FUNKSIYA
# ============================================
def generate_with_ai(request: AIRequest) -> AIResponse:
    """
    AI orqali jadval yaratish.

    Hozircha (3-bosqich): DEMO rejim.
    8-bosqichda: haqiqiy AI provayderiga ulanadi.

    Args:
        request: AIRequest — prompt va limitlar.

    Returns:
        AIResponse — xom AI javobi (validatsiyadan o'tmagan).

    Raises:
        RuntimeError: AI xizmati ishlamasa.
    """
    # 8-bosqichda bu yerda haqiqiy AI chaqiruvi bo'ladi
    # Hozircha demo rejim
    logger.info(f"Demo rejim ishga tushdi. Prompt: {request.prompt[:50]}...")

    return _get_demo_response(request.prompt)


def _get_demo_response(prompt: str) -> AIResponse:
    """
    Promptga mos demo javobni qaytarish.

    Kalit so'z qidirib, mos namunani qaytaradi.
    Topilmasa — DEFAULT_DEMO.
    """
    prompt_lower = prompt.lower()

    # Kalit so'zlarni qidirish
    for keyword, template in DEMO_TEMPLATES.items():
        if keyword in prompt_lower:
            logger.info(f"Demo namuna topildi: '{keyword}'")
            return AIResponse(
                title=template["title"],
                columns=template["columns"],
                rows=template["rows"],
            )

    # Standart
    logger.info("Standart demo namuna qaytarildi")
    return AIResponse(
        title=DEFAULT_DEMO["title"],
        columns=DEFAULT_DEMO["columns"],
        rows=DEFAULT_DEMO["rows"],
    )


def is_ai_available() -> bool:
    """
    AI provayderi mavjudligini tekshirish.

    Hozircha (3-bosqich): har doim False (demo rejim).
    8-bosqichda: API kalit bor-yo'qligini tekshiradi.
    """
    return bool(settings.ai_api_key and settings.ai_provider)