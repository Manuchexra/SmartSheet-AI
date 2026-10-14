"""
AI moduli xizmati.

Bu modul:
1. Foydalanuvchi promptini AI provayderiga yuboradi.
2. AI javobini qabul qiladi.
3. JSON'ni parse qiladi va validatsiya qiladi.
4. AI ishlamasa — demo rejimga o'tadi (fallback).
"""

import json
import logging
import re

import httpx

from backend.config import settings
from backend.modules.ai.prompts import build_system_prompt, build_user_prompt
from backend.modules.ai.schemas import (
    AIError,
    AIInvalidResponseError,
    AIRateLimitError,
    AIRequest,
    AIResponse,
    AITimeoutError,
)


logger = logging.getLogger(__name__)


# ============================================
# DEMO NAMUNALAR (fallback uchun)
# ============================================
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
def generate_with_ai(request: AIRequest) -> tuple[AIResponse, str]:
    """
    AI orqali jadval yaratish.

    Returns:
        (AIResponse, source) — javob va manba ('ai' | 'demo').
    """
    if not is_ai_available():
        logger.info("AI mavjud emas — demo rejim")
        return _get_demo_response(request.prompt), "demo"

    try:
        response = _call_ai_provider(request)
        return response, "ai"
    except (AITimeoutError, AIRateLimitError, AIInvalidResponseError) as e:
        logger.warning(f"AI xatosi: {e.code} — {e}")
        raise
    except AIError as e:
        logger.warning(f"AI xatosi: {e.code} — {e}")
        raise
    except Exception as e:
        logger.error(f"AI kutilmagan xato: {e}", exc_info=True)
        raise AIError(f"AI xizmatida xatolik: {e}") from e


def is_ai_available() -> bool:
    """AI provayderi sozlanganmi?"""
    return bool(
        settings.ai_api_key
        and settings.ai_provider
        and settings.ai_provider.lower() != "demo"
    )


# ============================================
# AI PROVAYDERIGA SO'ROV
# ============================================
def _call_ai_provider(request: AIRequest) -> AIResponse:
    """AI provayderiga HTTP so'rov yuborish."""
    if not settings.ai_api_url:
        raise AIError("AI_API_URL sozlanmagan")

    headers = {
        "Authorization": f"Bearer {settings.ai_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(request.prompt)},
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
    }

    logger.info(
        f"AI'ga so'rov: model={settings.ai_model}, "
        f"prompt_len={len(request.prompt)}"
    )

    # HTTP so'rov
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                settings.ai_api_url,
                headers=headers,
                json=payload,
            )
    except httpx.TimeoutException as e:
        raise AITimeoutError() from e
    except httpx.ConnectError as e:
        raise AIError("AI xizmatiga ulanib bo'lmadi") from e
    except httpx.HTTPError as e:
        raise AIError(f"AI so'rovida xato: {e}") from e

    # Status kod
    if response.status_code == 429:
        raise AIRateLimitError()
    if response.status_code == 401:
        raise AIError("AI API kaliti noto'g'ri")
    if response.status_code >= 500:
        raise AIError(f"AI provayderida xato: {response.status_code}")
    if response.status_code != 200:
        raise AIError(
            f"AI javobi: {response.status_code} — {response.text[:200]}"
        )

    # Javobni parse qilish
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise AIInvalidResponseError("AI JSON bo'lmagan javob qaytardi") from e

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise AIInvalidResponseError("AI javob formati noto'g'ri") from e

    parsed = _parse_json_content(content)

    try:
        return AIResponse(
            title=parsed.get("title", "Untitled"),
            columns=parsed.get("columns", []),
            rows=parsed.get("rows", []),
        )
    except Exception as e:
        raise AIInvalidResponseError(
            f"AI javobi validatsiyadan o'tmadi: {e}"
        ) from e


# ============================================
# JSON PARSE
# ============================================
def _parse_json_content(content: str) -> dict:
    """AI'dan kelgan matnni JSON'ga aylantirish."""
    if not content or not content.strip():
        raise AIInvalidResponseError("AI bo'sh javob qaytardi")

    text = content.strip()

    # 1. Markdown code fence'ni olib tashlash
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # 2. JSON boshlanishini topish
    start_idx = -1
    for i, ch in enumerate(text):
        if ch in "{[":
            start_idx = i
            break

    if start_idx == -1:
        raise AIInvalidResponseError("AI javobida JSON topilmadi")

    # 3. JSON tugashini topish
    end_idx = max(text.rfind("}"), text.rfind("]"))
    if end_idx == -1 or end_idx < start_idx:
        raise AIInvalidResponseError("AI JSON tugallanmagan")

    json_text = text[start_idx:end_idx + 1]

    # 4. Parse
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse xatosi: {e}\nMatn: {json_text[:500]}")
        raise AIInvalidResponseError(f"AI JSON noto'g'ri: {e}") from e


# ============================================
# DEMO REJIM (fallback)
# ============================================
def _get_demo_response(prompt: str) -> AIResponse:
    """Promptga mos demo javobni qaytarish."""
    prompt_lower = prompt.lower()

    for keyword, template in DEMO_TEMPLATES.items():
        if keyword in prompt_lower:
            logger.info(f"Demo namuna topildi: '{keyword}'")
            return AIResponse(
                title=template["title"],
                columns=template["columns"],
                rows=template["rows"],
            )

    logger.info("Standart demo namuna qaytarildi")
    return AIResponse(
        title=DEFAULT_DEMO["title"],
        columns=DEFAULT_DEMO["columns"],
        rows=DEFAULT_DEMO["rows"],
    )