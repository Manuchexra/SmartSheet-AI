"""
Excel endpointlari.

- POST /api/v1/excel/export — jadvalni .xlsx sifatida yuklab olish.
"""

import logging
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.modules.excel.schemas import ExcelExportRequest
from backend.modules.excel.service import generate_excel


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/excel", tags=["Excel"])

# Excel MIME turi
EXCEL_MIME = (
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet"
)


@router.post(
    "/export",
    summary="Excel fayl yuklab olish",
    description=(
        "Joriy jadval holatini .xlsx fayl sifatida qaytaradi. "
        "Fayl nomi: smartsheet.xlsx"
    ),
    responses={
        200: {
            "content": {EXCEL_MIME: {}},
            "description": "Excel fayl muvaffaqiyatli yaratildi",
        },
        400: {"description": "Noto'g'ri so'rov"},
        422: {"description": "Validatsiya xatosi"},
        500: {"description": "Excel yaratishda xato"},
    },
    response_class=StreamingResponse,
)
async def export_excel(request: ExcelExportRequest) -> StreamingResponse:
    """
    Jadvalni Excel faylga aylantirib, yuklab olish uchun qaytarish.

    Oqim:
    1. So'rovni TableData'ga aylantirish (validatsiya).
    2. Excel service orqali .xlsx yaratish.
    3. StreamingResponse sifatida qaytarish.
    """
    logger.info(f"Excel eksport so'rovi: '{request.title}'")

    # 1. Validatsiya (ExcelExportRequest → TableData)
    try:
        table_data = request.to_table_data()
    except ValueError as e:
        logger.error(f"Excel validatsiya xatosi: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Jadval ma'lumotlari noto'g'ri: {e}",
        ) from e

    # 2. Excel yaratish
    try:
        buffer = generate_excel(table_data)
    except ValueError as e:
        logger.error(f"Excel yaratish xatosi: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Excel kutilmagan xato: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Excel fayl yaratishda xatolik yuz berdi.",
        ) from e

    # 3. Fayl nomi (xavfsiz)
    filename = "smartsheet.xlsx"

    # 4. StreamingResponse
    return StreamingResponse(
        buffer,
        media_type=EXCEL_MIME,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(buffer.getbuffer().nbytes),
        },
    )