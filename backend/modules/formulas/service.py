"""
Formulas moduli xizmati.

Bu modul:
1. Formulalarni tekshiradi.
2. Xavfli formulalarni filtrlaydi.
3. Formula kolonkalarini aniqlaydi.
4. Excel'ga yozish uchun tayyorlaydi.
"""

import logging
import re

from backend.modules.formulas.schemas import CellFormula, FormulaType


logger = logging.getLogger(__name__)


# ============================================
# XAVFSIZ FORMULALAR RO'YXATI
# ============================================
# Faqat shu formulalarga ruxsat (whitelist)
SAFE_FORMULAS = {
    "SUM", "AVERAGE", "COUNT", "MAX", "MIN",
    "IF", "SUMIF", "COUNTIF", "CONCAT",
    "VLOOKUP", "ROUND", "ABS", "SQRT",
    "AND", "OR", "NOT", "IFERROR",
    "TODAY", "NOW", "DATE", "YEAR", "MONTH", "DAY",
    "UPPER", "LOWER", "TRIM", "LEN", "LEFT", "RIGHT", "MID",
}

# Xavfli formulalar (bloklanadi)
DANGEROUS_FORMULAS = {
    "HYPERLINK", "WEBSERVICE", "IMPORTXML", "IMPORTHTML",
    "IMPORTDATA", "IMPORTFEED", "IMPORTRANGE",
    "EXEC", "SYSTEM", "CMD", "SHELL",
}


# ============================================
# FORMULA ANIQLASH
# ============================================
def detect_formula_type(formula: str) -> FormulaType | None:
    """
    Formula turini aniqlash.
    
    Args:
        formula: Excel formula (=SUM(...))
    
    Returns:
        FormulaType yoki None
    """
    if not formula or not formula.startswith("="):
        return None
    
    # =SUM(...) → SUM
    match = re.match(r"^=([A-Z]+)\(", formula.upper())
    if not match:
        return None
    
    func_name = match.group(1)
    
    try:
        return FormulaType(func_name)
    except ValueError:
        return None


def is_formula_safe(formula: str) -> bool:
    """
    Formula xavfsizligini tekshirish.
    
    Xavfli formulalar (HYPERLINK, EXEC, ...) bloklanadi.
    """
    if not formula or not formula.startswith("="):
        return False
    
    formula_upper = formula.upper()
    
    # Xavfli formulalarni tekshirish
    for dangerous in DANGEROUS_FORMULAS:
        if dangerous in formula_upper:
            logger.warning(f"Xavfli formula bloklandi: {dangerous}")
            return False
    
    # Ruxsat etilgan formulalarni tekshirish
    match = re.match(r"^=([A-Z]+)\(", formula_upper)
    if not match:
        # =A1+B1 kabi oddiy ifodalar (ruxsat)
        return True
    
    func_name = match.group(1)
    return func_name in SAFE_FORMULAS


def is_cell_formula(value) -> bool:
    """
    Qiymat formula ekanligini tekshirish.
    
    Formula = bilan boshlanadi.
    """
    if not isinstance(value, str):
        return False
    return value.startswith("=") and len(value) > 1


# ============================================
# FORMULA VALIDATSIYA
# ============================================
def validate_formulas(formulas: list[CellFormula]) -> list[CellFormula]:
    """
    Formulalar ro'yxatini validatsiya qilish.
    
    - Xavfli formulalarni olib tashlash
    - Noto'g'ri katak manzillarini olib tashlash
    - Formula turini tekshirish
    """
    valid = []
    
    for formula in formulas:
        # Katak manzili
        if not re.match(r"^[A-Z]+\d+$", formula.cell):
            logger.warning(f"Noto'g'ri katak: {formula.cell}")
            continue
        
        # Xavfsizlik
        if not is_formula_safe(formula.formula):
            logger.warning(f"Xavfli formula: {formula.formula}")
            continue
        
        valid.append(formula)
    
    return valid


# ============================================
# YORDAMCHI: FORMULA YARATISH
# ============================================
def build_sum_formula(col_letter: str, first_row: int, last_row: int) -> str:
    """SUM formula yaratish."""
    return f"=SUM({col_letter}{first_row}:{col_letter}{last_row})"


def build_average_formula(col_letter: str, first_row: int, last_row: int) -> str:
    """AVERAGE formula yaratish."""
    return f"=AVERAGE({col_letter}{first_row}:{col_letter}{last_row})"


def build_if_formula(
    condition_cell: str,
    operator: str,
    value: str,
    true_text: str,
    false_text: str,
) -> str:
    """IF formula yaratish."""
    return f'=IF({condition_cell}{operator}{value},"{true_text}","{false_text}")'


def col_index_to_letter(index: int) -> str:
    """
    Ustun raqamini harfga aylantirish.
    
    0 → A, 1 → B, ..., 25 → Z, 26 → AA
    """
    result = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result