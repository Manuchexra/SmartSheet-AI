"""
Excel moduli xizmati.

Bu modul:
1. TableData'dan .xlsx fayl yaratadi.
2. Ustun sarlavhalarini yozadi.
3. Formulalarni Excel formulalari sifatida yozadi.
4. Formatlash qo'llaydi (qalin sarlavha, kenglik, filter, freeze).
5. Faylni BytesIO sifatida qaytaradi (yuklab olish uchun).

11-bosqich: Excel formulalar qo'llab-quvvatlanadi.
"""

import logging
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from backend.modules.formulas.service import is_formula_safe
from backend.modules.table_generator.schemas import TableData


logger = logging.getLogger(__name__)


# ============================================
# FORMATLASH KONSTANTALARI
# ============================================
HEADER_FONT = Font(
    name="Calibri",
    size=11,
    bold=True,
    color="FFFFFF",
)

HEADER_FILL = PatternFill(
    start_color="2563EB",  # primary blue
    end_color="2563EB",
    fill_type="solid",
)

HEADER_ALIGNMENT = Alignment(
    horizontal="center",
    vertical="center",
    wrap_text=True,
)

HEADER_BORDER = Border(
    left=Side(style="thin", color="1E40AF"),
    right=Side(style="thin", color="1E40AF"),
    top=Side(style="thin", color="1E40AF"),
    bottom=Side(style="thin", color="1E40AF"),
)

CELL_ALIGNMENT = Alignment(
    horizontal="left",
    vertical="top",
    wrap_text=False,
)

# Formula kataklari uchun font (ko'k, italic)
FORMULA_FONT = Font(
    name="Calibri",
    size=11,
    color="1E40AF",  # ko'k
    italic=True,
)

FORMULA_FILL = PatternFill(
    start_color="EFF6FF",  # och ko'k
    end_color="EFF6FF",
    fill_type="solid",
)

# Xavfli Excel formulalar (formula injection oldini olish)
# Agar katak shu belgilardan biri bilan boshlansa, apostrof qo'shamiz
DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


# ============================================
# ASOSIY FUNKSIYA
# ============================================
def generate_excel(table_data: TableData) -> BytesIO:
    """
    TableData'dan Excel fayl yaratish.

    Formulalar (="..." bilan boshlanadigan) Excel formulalari sifatida yoziladi.
    Ular Excel'da ochilganda avtomatik hisoblanadi.

    Args:
        table_data: Validatsiyadan o'tgan jadval.

    Returns:
        BytesIO — fayl baytlari.

    Raises:
        ValueError: Jadval bo'sh bo'lsa.
    """
    if not table_data.columns:
        raise ValueError("Ustunlar bo'sh — Excel yaratib bo'lmaydi")

    if not table_data.rows:
        raise ValueError("Qatorlar bo'sh — Excel yaratib bo'lmaydi")

    wb = Workbook()
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.calculation.calcMode = "auto"
    ws = wb.active
    ws.title = _safe_sheet_title(table_data.title)

    # ============================================
    # 1. USTUN SARLAVHALARI (1-qator)
    # ============================================
    for col_idx, col_name in enumerate(table_data.columns, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.value = _sanitize_value(col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGNMENT
        cell.border = HEADER_BORDER

    # ============================================
    # 2. MA'LUMOTLAR (2-qatordan boshlab)
    # ============================================
    formula_count = 0

    for row_idx, row in enumerate(table_data.rows, start=2):
        for col_idx, value in enumerate(row, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)

            # ============================================
            # FORMULA EKANLIGINI TEKSHIRISH
            # ============================================
            if _is_formula(value) and is_formula_safe(value):
                # Excel formula sifatida yozish
                cell.value = value

                # Formula kataklarini maxsus belgilash
                cell.font = FORMULA_FONT
                cell.fill = FORMULA_FILL
                cell.alignment = CELL_ALIGNMENT

                formula_count += 1
            else:
                # Oddiy qiymat
                cell.value = _sanitize_value(value)
                cell.alignment = CELL_ALIGNMENT

    # ============================================
    # 3. USTUN KENGLIKLARI
    # ============================================
    for col_idx in range(1, len(table_data.columns) + 1):
        letter = get_column_letter(col_idx)
        max_length = _calculate_column_width(
            table_data.columns[col_idx - 1],
            [row[col_idx - 1] for row in table_data.rows],
        )
        ws.column_dimensions[letter].width = max_length

    # ============================================
    # 4. QATOR BALANDLIGI (sarlavha)
    # ============================================
    ws.row_dimensions[1].height = 28

    # ============================================
    # 5. FREEZE PANES (sarlavhani muzlatish)
    # ============================================
    ws.freeze_panes = "A2"

    # ============================================
    # 6. AUTO FILTER
    # ============================================
    last_col_letter = get_column_letter(len(table_data.columns))
    last_row = len(table_data.rows) + 1  # +1 sarlavha uchun
    ws.auto_filter.ref = f"A1:{last_col_letter}{last_row}"

    # ============================================
    # 7. FAYLNI XOTIRAGA YOZISH
    # ============================================
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    logger.info(
        f"Excel yaratildi: '{table_data.title}' — "
        f"{table_data.row_count} qator × {table_data.column_count} ustun, "
        f"formulalar: {formula_count}"
    )

    return buffer


# ============================================
# YORDAMCHI FUNKSIYALAR
# ============================================
def _sanitize_value(value: Any) -> Any:
    """
    Xavfli Excel formulalarini neytrallashtirish.

    Diqqat: bu funksiya FAQAT oddiy qiymatlar uchun.
    Formulalar alohida ishlanadi (ularni apostrof qo'shish mumkin emas).

    Agar qiymat '=', '+', '-', '@', '\\t', '\\r' bilan boshlansa,
    oldiga apostrof qo'shamiz — Excel uni matn deb o'qiydi.
    """
    if value is None:
        return ""

    if isinstance(value, (int, float, bool)):
        return value

    text = str(value)

    # Formula injection oldini olish
    if text and text[0] in DANGEROUS_PREFIXES:
        return "'" + text

    return text


def _is_formula(value: Any) -> bool:
    """
    Qiymat formula ekanligini tekshirish.

    Formula = "=" bilan boshlanadi va uzunligi 1 dan katta.
    """
    return (
        isinstance(value, str)
        and value.startswith("=")
        and len(value) > 1
    )


def _calculate_column_width(header: str, values: list) -> float:
    """
    Ustun kengligini hisoblash.

    Formula uchun kengroq (natija uzunroq bo'lishi mumkin).
    Sarlavha va qiymatlar orasidagi maksimal uzunlik + padding.
    """
    header_len = len(str(header)) if header else 0

    max_value_len = 0
    for v in values[:50]:  # Faqat birinchi 50 qatorni tekshiramiz (tezlik uchun)
        if v is None:
            continue

        text = str(v)

        # Formula bo'lsa — o'rtacha kenglik (natija qisqaroq)
        if _is_formula(v):
            max_value_len = max(max_value_len, min(len(text), 25))
        else:
            max_value_len = max(max_value_len, len(text))

    # Sarlavha + 4 belgi padding, minimal 10, maksimal 50
    width = max(header_len + 4, max_value_len + 2, 10)
    return min(width, 50)


def _safe_sheet_title(title: str) -> str:
    """
    Excel varaq nomini xavfsiz qilish.

    Excel qoidalari:
    - 31 belgidan oshmasin
    - \\ / * ? : [ ] belgilari bo'lmasin
    """
    if not title:
        return "Sheet1"

    # Xavfli belgilarni olib tashlash
    for ch in ['\\', '/', '*', '?', ':', '[', ']']:
        title = title.replace(ch, '')

    # 31 belgi bilan cheklash
    title = title.strip()[:31]

    return title or "Sheet1"