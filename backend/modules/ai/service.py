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
from backend.modules.ai.prompts import (
    build_edit_system_prompt,
    build_edit_user_prompt,
    build_system_prompt,
    build_user_prompt,
)

from backend.modules.ai.schemas import (
    AIError,
    AIInvalidResponseError,
    AIRateLimitError,
    AIRequest,
    AIResponse,
    AITimeoutError,
)
from backend.modules.styles.schemas import merge_style_overrides, normalize_styles
from backend.modules.styles.service import apply_style_request


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

SPREADSHEET_INTENT_TERMS = (
    "jadval",
    "ro'yxat",
    "royxat",
    "roʻyxat",
    "ro‘yxat",
    "table",
    "spreadsheet",
    "excel",
    "sheet",
    "ustun",
    "qator",
    "таблица",
    "список",
)

# ============================================
# ASOSIY FUNKSIYA
# ============================================
def generate_with_ai(request: AIRequest) -> tuple[AIResponse, str]:
    """
    AI orqali jadval yaratish.

    Returns:
        (AIResponse, source) — javob va manba ('ai' | 'demo').
    """
    if not _is_spreadsheet_request(request.prompt):
        logger.info("Jadval so'rovi aniqlanmadi — matn bitta katakka yoziladi")
        return _get_text_response(request.prompt), "demo"

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


def _is_spreadsheet_request(prompt: str) -> bool:
    """Return whether a prompt clearly asks for spreadsheet data."""
    normalized_prompt = prompt.casefold()
    return any(term in normalized_prompt for term in SPREADSHEET_INTENT_TERMS) or any(
        keyword in normalized_prompt for keyword in DEMO_TEMPLATES
    )


def _get_text_response(prompt: str) -> AIResponse:
    """Preserve non-spreadsheet messages as a single cell instead of inventing data."""
    text = prompt.strip()
    return AIResponse(
        title=text[:60] or "Xabar",
        columns=["Matn"],
        rows=[[text]],
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
            styles=parsed.get("styles"),
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

    logger.info("Mos demo jadval topilmadi — prompt matni saqlanadi")
    return _get_text_response(prompt)


# ============================================
# AI EDIT (12.7-bosqich)
# ============================================
def generate_edit_with_ai(
    user_request: str,
    existing_table: dict,
) -> tuple[AIResponse, str]:
    """
    Mavjud jadvalni AI orqali tahrirlash.

    Args:
        user_request: Foydalanuvchi so'rovi (masalan, "Maoshni 10% oshir")
        existing_table: Mavjud jadval dict ko'rinishida
            {"title": "...", "columns": [...], "rows": [...]}

    Returns:
        (AIResponse, source) — yangilangan jadval va manba.
    """
    if not is_ai_available():
        logger.info("AI mavjud emas — demo edit")
        return _get_demo_edit_response(user_request, existing_table), "demo"

    # JSON'ni string'ga aylantirish (AI'ga yuborish uchun)
    import json
    table_json = json.dumps(existing_table, ensure_ascii=False, indent=2)

    # AI'ga so'rov
    try:
        response = _call_ai_edit_provider(
            user_request,
            table_json,
            existing_table,
        )
        explicit_styles = apply_style_request(
            user_request,
            existing_table.get("columns", []),
            existing_table.get("styles"),
        )
        if explicit_styles is not None:
            response = AIResponse(
                title=response.title,
                columns=response.columns,
                rows=response.rows,
                styles=explicit_styles,
            )
        return response, "ai"
    except (AITimeoutError, AIRateLimitError, AIInvalidResponseError) as e:
        logger.warning(f"AI edit xatosi: {e.code} — {e}")
        raise
    except AIError as e:
        logger.warning(f"AI edit xatosi: {e.code} — {e}")
        raise
    except Exception as e:
        logger.error(f"AI edit kutilmagan xato: {e}", exc_info=True)
        raise AIError(f"AI edit xatosi: {e}") from e


def _call_ai_edit_provider(
    user_request: str,
    table_json: str,
    existing_table: dict,
) -> AIResponse:
    """AI provayderiga edit so'rovini yuborish."""
    if not settings.ai_api_url:
        raise AIError("AI_API_URL sozlanmagan")

    headers = {
        "Authorization": f"Bearer {settings.ai_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": build_edit_system_prompt()},
            {
                "role": "user",
                "content": build_edit_user_prompt(table_json, user_request),
            },
        ],
        "temperature": 0.2,  # Past harorat — aniqroq
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
    }

    logger.info(f"AI edit so'rovi: model={settings.ai_model}")

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

    # Status
    if response.status_code == 429:
        raise AIRateLimitError()
    if response.status_code == 401:
        raise AIError("AI API kaliti noto'g'ri")
    if response.status_code >= 500:
        raise AIError(f"AI provayderida xato: {response.status_code}")
    if response.status_code != 200:
        raise AIError(f"AI javobi: {response.status_code} — {response.text[:200]}")

    # Parse
    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise AIInvalidResponseError("AI javob formati noto'g'ri") from e

    parsed = _parse_json_content(content)

    try:
        return AIResponse(
            title=parsed.get("title", existing_table.get("title", "Untitled")),
            columns=parsed.get("columns", existing_table.get("columns", [])),
            rows=parsed.get("rows", existing_table.get("rows", [])),
            styles=merge_style_overrides(
                normalize_styles(existing_table.get("styles")),
                parsed.get("styles", {}),
            ),
        )
    except Exception as e:
        raise AIInvalidResponseError(f"AI javobi validatsiyadan o'tmadi: {e}") from e


def _get_demo_edit_response(
    user_request: str,
    existing_table: dict,
) -> AIResponse:
    """
    Demo edit — AI mavjud emas.

    Oddiy o'zgartirishlarni qo'llab-quvvatlaydi:
    - "10% oshir" — raqamlarni 10% oshirish
    - "rangini o'zgartir" — o'zgarishsiz qaytarish
    - boshqa — o'zgarishsiz qaytarish
    """
    import re

    title = existing_table.get("title", "Jadval")
    columns = existing_table.get("columns", [])
    rows = existing_table.get("rows", [])
    styles = normalize_styles(existing_table.get("styles"))

    request_lower = user_request.lower()

    # "10% oshir" kabi so'rovlarni qayta ishlash
    percent_match = re.search(r"(\d+)\s*%", request_lower)
    if percent_match and any(
        kw in request_lower for kw in ["oshir", "ko'paytir", "increase", "qo'sh"]
    ):
        percent = int(percent_match.group(1)) / 100
        new_rows = []
        for row in rows:
            new_row = []
            for cell in row:
                if isinstance(cell, (int, float)):
                    new_row.append(round(cell * (1 + percent), 2))
                else:
                    new_row.append(cell)
            new_rows.append(new_row)
        return AIResponse(title=title, columns=columns, rows=new_rows, styles=styles)

    updated_styles = apply_style_request(user_request, columns, styles)
    if updated_styles is not None:
        return AIResponse(
            title=title,
            columns=columns,
            rows=rows,
            styles=updated_styles,
        )

    # Boshqa so'rovlar — o'zgarishsiz qaytarish
    logger.info(f"Demo edit: o'zgarishsiz qaytarildi")
    return AIResponse(title=title, columns=columns, rows=rows, styles=styles)