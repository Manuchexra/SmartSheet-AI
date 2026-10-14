"""
Table Generator moduli xizmati.

Bu modul:
1. AI'dan kelgan xom javobni tekshiradi.
2. Jadval strukturasini validatsiya qiladi.
3. TableData'ga aylantiradi.
4. TableGenerateResponse qaytaradi.
"""

import logging

from pydantic import ValidationError

from backend.config import settings
from backend.modules.ai.schemas import AIResponse
from backend.modules.table_generator.schemas import (
    TableData,
    TableGenerateResponse,
)


logger = logging.getLogger(__name__)


# ============================================
# ASOSIY FUNKSIYA
# ============================================
def build_table_response(
    ai_response: AIResponse,
    source: str = "ai",
) -> TableGenerateResponse:
    """
    AI javobini TableData'ga aylantirib, API javobini tayyorlash.

    Bu funksiya:
    1. AI javobini TableData orqali validatsiya qiladi.
    2. Limitlarni tekshiradi (max_rows, max_columns).
    3. TableGenerateResponse qaytaradi.

    Args:
        ai_response: AI'dan kelgan xom javob.
        source: 'ai' yoki 'demo'.

    Returns:
        TableGenerateResponse — tayyor API javobi.

    Raises:
        ValueError: AI javobi noto'g'ri bo'lsa.
    """
    try:
        # TableData orqali to'liq validatsiya
        table_data = TableData(
            title=ai_response.title,
            columns=ai_response.columns,
            rows=ai_response.rows,
        )
    except ValidationError as e:
        logger.error(f"AI javobi validatsiyadan o'tmadi: {e}")
        raise ValueError(f"AI javobi noto'g'ri formatda: {e}") from e

    # Limitlarni qo'shimcha tekshirish (TableData allaqachon tekshirgan,
    # lekin bu yerda aniqroq xabar berish uchun)
    if table_data.row_count > settings.max_rows:
        raise ValueError(
            f"Jadval juda katta: {table_data.row_count} qator "
            f"(maksimal: {settings.max_rows})"
        )

    if table_data.column_count > settings.max_columns:
        raise ValueError(
            f"Jadval juda ko'p ustunli: {table_data.column_count} "
            f"(maksimal: {settings.max_columns})"
        )

    # Javobni qurish
    response = TableGenerateResponse.from_table_data(table_data, source=source)

    logger.info(
        f"Jadval tayyor: '{response.title}' — "
        f"{response.row_count} qator × {response.column_count} ustun "
        f"(source={source})"
    )

    return response


def validate_table_data(data: dict) -> TableData:
    """
    Xom dict'ni TableData'ga aylantirish va validatsiya qilish.

    Bu Excel moduli ham ishlatadi.

    Args:
        data: Xom dict (title, columns, rows).

    Returns:
        TableData — validatsiyadan o'tgan jadval.

    Raises:
        ValueError: Ma'lumot noto'g'ri bo'lsa.
    """
    try:
        return TableData(**data)
    except ValidationError as e:
        logger.error(f"Jadval ma'lumotlari noto'g'ri: {e}")
        raise ValueError(f"Jadval ma'lumotlari noto'g'ri: {e}") from e