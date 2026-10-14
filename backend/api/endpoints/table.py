"""
Table endpointlari.

- POST /api/v1/tables/generate — jadval yaratish.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.config import settings
from backend.modules.ai.schemas import (
    AIError,
    AIInvalidResponseError,
    AIRateLimitError,
    AIRequest,
    AITimeoutError,
)
from backend.modules.ai.service import generate_with_ai, _get_demo_response
from backend.modules.table_generator.schemas import (
    TableGenerateRequest,
    TableGenerateResponse,
)
from backend.modules.table_generator.service import build_table_response


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tables", tags=["Tables"])


# ============================================
# POST /api/v1/tables/generate
# ============================================
@router.post(
    "/generate",
    response_model=TableGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Jadval yaratish",
    description=(
        "Foydalanuvchi promptini AI orqali tahlil qilib, "
        "strukturali jadval qaytaradi. "
        "AI mavjud bo'lmasa yoki xato bersa — demo rejimga o'tadi."
    ),
    responses={
        400: {"description": "Noto'g'ri so'rov"},
        422: {"description": "Validatsiya xatosi"},
        502: {"description": "AI xizmatidan noto'g'ri javob"},
        503: {"description": "AI xizmati mavjud emas"},
        500: {"description": "Kutilmagan xato"},
    },
)
async def generate_table(request: TableGenerateRequest) -> TableGenerateResponse:
    """
    Foydalanuvchi promptidan jadval yaratish.

    Oqim:
    1. Prompt validatsiyasi (Pydantic).
    2. AI moduliga so'rov — `(AIResponse, source)` qaytaradi.
    3. AI javobini validatsiya qilish.
    4. AI xatosi bo'lsa — demo rejimga fallback.
    """
    logger.info(f"Yangi so'rov: '{request.prompt[:80]}...'")

    # AIRequest'ni tayyorlash
    ai_request = AIRequest(
        prompt=request.prompt,
        max_rows=settings.max_rows,
        max_columns=settings.max_columns,
    )

    # ============================================
    # 1. AI'ga so'rov (yoki demo)
    # ============================================
    # MUHIM: generate_with_ai endi TUPLE qaytaradi: (AIResponse, source)
    ai_response = None
    source = "demo"

    try:
        ai_response, source = generate_with_ai(ai_request)
        logger.info(f"AI muvaffaqiyatli javob berdi (source={source})")

    except AITimeoutError as e:
        logger.warning(f"AI timeout: {e}")
        ai_response = _get_demo_response(request.prompt)
        source = "demo"

    except AIRateLimitError as e:
        logger.warning(f"AI rate limit: {e}")
        ai_response = _get_demo_response(request.prompt)
        source = "demo"

    except AIInvalidResponseError as e:
        logger.warning(f"AI noto'g'ri javob: {e}")
        ai_response = _get_demo_response(request.prompt)
        source = "demo"

    except AIError as e:
        logger.warning(f"AI xatosi: {e.code} — {e}")
        # AI umuman ishlamasa — demo rejimga fallback
        ai_response = _get_demo_response(request.prompt)
        source = "demo"

    except Exception as e:
        logger.error(f"AI kutilmagan xato: {e}", exc_info=True)
        # Kutilmagan xato bo'lsa ham — demo rejimga fallback
        ai_response = _get_demo_response(request.prompt)
        source = "demo"

    # Xavfsizlik: agar biror sabab bilan ai_response None bo'lsa
    if ai_response is None:
        logger.error("AI response None — demo rejimga o'tish")
        ai_response = _get_demo_response(request.prompt)
        source = "demo"

    # ============================================
    # 2. Javobni validatsiya qilish
    # ============================================
    try:
        response = build_table_response(ai_response, source=source)
    except ValueError as e:
        logger.error(f"Jadval validatsiyasi xatosi: {e}")

        # AI noto'g'ri jadval yaratdi — demo'ga fallback
        try:
            demo_response = _get_demo_response(request.prompt)
            response = build_table_response(demo_response, source="demo")
        except ValueError as e2:
            logger.error(f"Demo ham ishlamadi: {e2}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Jadval yaratishda xatolik yuz berdi.",
            ) from e2

    # ============================================
    # 3. Javob qaytarish
    # ============================================
    logger.info(
        f"Jadval tayyor: {response.row_count}×{response.column_count} "
        f"(source={response.source})"
    )
    return response