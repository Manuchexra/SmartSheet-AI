"""
Table endpointlari.

Bu fayl jadval yaratish endpointini belgilaydi:
- POST /api/v1/tables/generate
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.config import settings
from backend.modules.ai.schemas import AIRequest
from backend.modules.ai.service import generate_with_ai, is_ai_available
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
        "AI mavjud bo'lmasa, demo rejimda ishlaydi."
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
    2. AI moduliga so'rov yuborish (yoki demo).
    3. AI javobini validatsiya qilish.
    4. TableGenerateResponse qaytarish.

    Args:
        request: Foydalanuvchi prompti.

    Returns:
        TableGenerateResponse — tayyor jadval.

    Raises:
        HTTPException: Har qanday xatolik yuz bersa.
    """
    logger.info(f"Yangi so'rov: '{request.prompt[:80]}...'")

    # ============================================
    # 1. AI yoki demo rejimni aniqlash
    # ============================================
    ai_available = is_ai_available()
    source = "ai" if ai_available else "demo"

    if not ai_available:
        logger.info("AI mavjud emas — demo rejim ishlatiladi")

    # ============================================
    # 2. AI moduliga so'rov
    # ============================================
    try:
        ai_request = AIRequest(
            prompt=request.prompt,
            max_rows=settings.max_rows,
            max_columns=settings.max_columns,
        )
        ai_response = generate_with_ai(ai_request)

    except TimeoutError as e:
        logger.error(f"AI timeout: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "AI xizmati javob bermadi. Iltimos, birozdan so'ng "
                "qayta urinib ko'ring."
            ),
        ) from e

    except ConnectionError as e:
        logger.error(f"AI ulanish xatosi: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI xizmatiga ulanib bo'lmadi. Internetni tekshiring.",
        ) from e

    except Exception as e:
        logger.error(f"AI kutilmagan xato: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI xizmatidan noto'g'ri javob keldi.",
        ) from e

    # ============================================
    # 3. Javobni validatsiya qilish
    # ============================================
    try:
        response = build_table_response(ai_response, source=source)

    except ValueError as e:
        logger.error(f"Jadval validatsiyasi xatosi: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI yaratgan jadval noto'g'ri: {e}",
        ) from e

    # ============================================
    # 4. Javob qaytarish
    # ============================================
    logger.info(
        f"Jadval muvaffaqiyatli yaratildi: "
        f"{response.row_count}×{response.column_count} (source={source})"
    )
    return response