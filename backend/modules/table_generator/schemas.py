"""
Table Generator modulining sxemalari.

Bu modul jadvalning asosiy tuzilmasini belgilaydi:
- TableData — to'liq jadval (title, columns, rows)
- TableGenerateRequest — foydalanuvchi so'rovi (prompt)
- TableGenerateResponse — API javobi (jadval + metadata)
"""

from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator

from backend.config import settings


# ============================================
# ASOSIY JADVAL TUZILMASI
# ============================================
class TableData(BaseModel):
    """
    Jadvalning asosiy tuzilmasi.
    
    Bu sxema AI moduli, Excel moduli va API layer tomonidan
    birgalikda ishlatiladi.
    
    Misol:
        {
            "title": "Talabalar natijalari",
            "columns": ["Ism", "Familiya", "Ball"],
            "rows": [["Ali", "Karimov", 92], ["Malika", "Azizova", 85]]
        }
    """
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Jadval nomi (sarlavhasi)",
        examples=["Talabalar natijalari"],
    )
    
    columns: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,  # settings.max_columns
        description="Ustun sarlavhalari ro'yxati",
        examples=[["Ism", "Familiya", "Ball"]],
    )
    
    rows: list[list[Any]] = Field(
        ...,
        description="Qatorlar ro'yxati. Har bir qator — qiymatlar ro'yxati.",
        examples=[[["Ali", "Karimov", 92], ["Malika", "Azizova", 85]]],
    )
    
    # ---------- VALIDATSIYA ----------
    
    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Sarlavha bo'sh bo'lmasligi kerak."""
        v = v.strip()
        if not v:
            raise ValueError("Jadval nomi bo'sh bo'lishi mumkin emas")
        return v
    
    @field_validator("columns")
    @classmethod
    def columns_not_empty(cls, v: list[str]) -> list[str]:
        """Ustunlar ro'yxati bo'sh bo'lmasligi va har biri bo'sh bo'lmasligi kerak."""
        if not v:
            raise ValueError("Kamida bitta ustun bo'lishi kerak")
        
        cleaned = []
        for i, col in enumerate(v):
            col_clean = str(col).strip()
            if not col_clean:
                raise ValueError(f"{i + 1}-ustun nomi bo'sh bo'lishi mumkin emas")
            cleaned.append(col_clean)
        
        # Takrorlanuvchi ustunlarni tekshirish
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Ustun nomlari takrorlanmasligi kerak")
        
        return cleaned
    
    @field_validator("rows")
    @classmethod
    def rows_not_empty(cls, v: list[list[Any]]) -> list[list[Any]]:
        """Kamida bitta qator bo'lishi kerak."""
        if not v:
            raise ValueError("Kamida bitta qator bo'lishi kerak")
        return v
    
    @model_validator(mode="after")
    def validate_structure(self) -> "TableData":
        """
        Ustunlar soni va qatorlar soni mosligini tekshirish.
        
        Bu — eng muhim tekshiruv:
        - Har bir qatordagi qiymatlar soni = ustunlar soni
        - Qatorlar soni limitdan oshmaydi
        - Ustunlar soni limitdan oshmaydi
        """
        n_cols = len(self.columns)
        n_rows = len(self.rows)
        
        # Limitlar
        if n_cols > settings.max_columns:
            raise ValueError(
                f"Ustunlar soni {settings.max_columns} tadan oshmasligi kerak "
                f"(hozir: {n_cols})"
            )
        
        if n_rows > settings.max_rows:
            raise ValueError(
                f"Qatorlar soni {settings.max_rows} tadan oshmasligi kerak "
                f"(hozir: {n_rows})"
            )
        
        # Har bir qatorning ustunlar soni mos kelishi
        for i, row in enumerate(self.rows):
            if len(row) != n_cols:
                raise ValueError(
                    f"{i + 1}-qatorda {len(row)} ta qiymat bor, "
                    f"lekin {n_cols} ta ustun kutilgan"
                )
        
        return self
    
    # ---------- YORDAMCHI XOSSALAR ----------
    
    @property
    def row_count(self) -> int:
        """Qatorlar soni."""
        return len(self.rows)
    
    @property
    def column_count(self) -> int:
        """Ustunlar soni."""
        return len(self.columns)


# ============================================
# JADVAL YARATISH — SO'ROV
# ============================================
class TableGenerateRequest(BaseModel):
    """
    Foydalanuvchidan keladigan jadval yaratish so'rovi.
    
    Misol:
        {"prompt": "Talabalar uchun 10 qatorli jadval yarat"}
    """
    
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=2000,  # settings.max_prompt_length
        description="Foydalanuvchining tabiiy tildagi so'rovi",
        examples=["Talabalar uchun 10 qatorli jadval yarat"],
    )
    
    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        """Prompt bo'sh bo'lmasligi va juda uzun bo'lmasligi kerak."""
        v = v.strip()
        if not v:
            raise ValueError("Prompt bo'sh bo'lishi mumkin emas")
        if len(v) > settings.max_prompt_length:
            raise ValueError(
                f"Prompt {settings.max_prompt_length} belgidan oshmasligi kerak "
                f"(hozir: {len(v)})"
            )
        return v


# ============================================
# JADVAL YARATISH — JAVOB
# ============================================
class TableGenerateResponse(BaseModel):
    """
    Jadval yaratish endpointining javobi.
    
    TableData + qo'shimcha metadata (source, row_count, column_count).
    """
    
    title: str = Field(..., description="Jadval nomi")
    columns: list[str] = Field(..., description="Ustun sarlavhalari")
    rows: list[list[Any]] = Field(..., description="Jadval qatorlari")
    row_count: int = Field(..., ge=0, description="Qatorlar soni")
    column_count: int = Field(..., ge=1, description="Ustunlar soni")
    source: str = Field(
        ...,
        description="Jadval manbasi: 'ai' yoki 'demo'",
        pattern="^(ai|demo)$",
    )
    
    @classmethod
    def from_table_data(cls, data: TableData, source: str) -> "TableGenerateResponse":
        """
        TableData obyektidan javob yaratish.
        
        Bu — DRY tamoyili: TableData'ni qayta yozmaslik uchun
        yordamchi metod.
        """
        return cls(
            title=data.title,
            columns=data.columns,
            rows=data.rows,
            row_count=data.row_count,
            column_count=data.column_count,
            source=source,
        )