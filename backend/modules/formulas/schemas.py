"""
Formulas moduli sxemalari.

Bu modul Excel formulalarini (SUM, AVERAGE, IF, ...) 
aniqlash va tekshirish uchun tuzilmalar.
"""

from enum import Enum
from pydantic import BaseModel, Field


# ============================================
# FORMULA TURLARI
# ============================================
class FormulaType(str, Enum):
    """Qo'llab-quvvatlanadigan Excel formulalari."""
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    COUNT = "COUNT"
    MAX = "MAX"
    MIN = "MIN"
    IF = "IF"
    SUMIF = "SUMIF"
    COUNTIF = "COUNTIF"
    CONCAT = "CONCAT"
    VLOOKUP = "VLOOKUP"
    ROUND = "ROUND"
    PERCENTAGE = "PERCENTAGE"


# ============================================
# FORMULA SXEMASI
# ============================================
class CellFormula(BaseModel):
    """
    Bitta katak uchun formula.
    
    Misol:
        {
            "cell": "C2",
            "formula": "=IF(B2>60,\"O'tdi\",\"Yiqildi\")",
            "type": "IF"
        }
    """
    
    cell: str = Field(
        ...,
        description="Katak manzili (A1, B2, C3, ...)",
        pattern=r"^[A-Z]+\d+$",
        examples=["C2", "D5", "E10"],
    )
    
    formula: str = Field(
        ...,
        description="Excel formula (= bilan boshlanadi)",
        min_length=2,
        examples=['=SUM(B2:B10)', '=IF(B2>60,"O\'tdi","Yiqildi")'],
    )
    
    formula_type: FormulaType = Field(
        ...,
        description="Formula turi",
    )
    
    description: str = Field(
        default="",
        max_length=200,
        description="Formula tavsifi (foydalanuvchi uchun)",
    )


class TableFormulas(BaseModel):
    """
    Jadval uchun barcha formulalar.
    
    Misol:
        {
            "cells": [
                {"cell": "C2", "formula": "=IF(B2>60,...)", "formula_type": "IF"},
                {"cell": "C3", "formula": "=IF(B3>60,...)", "formula_type": "IF"}
            ],
            "summary_row": {
                "label": "JAMI",
                "columns": {
                    "B": "=SUM(B2:B10)"
                }
            }
        }
    """
    
    cells: list[CellFormula] = Field(
        default_factory=list,
        description="Katak formulalari (har bir katak uchun)",
    )
    
    summary_rows: list[dict] = Field(
        default_factory=list,
        description="Yakuniy qatorlar (JAMI, O'RTACHA, ...)",
    )


# ============================================
# AI UCHUN FORMULA SO'ROVI
# ============================================
class FormulaGenerationRequest(BaseModel):
    """AI'ga formula yaratish uchun so'rov."""
    
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Foydalanuvchi so'rovi",
    )
    
    columns: list[str] = Field(
        ...,
        description="Jadval ustunlari",
    )
    
    sample_rows: list[list] = Field(
        default_factory=list,
        description="Namuna qatorlar (AI'ga kontekst uchun)",
    )