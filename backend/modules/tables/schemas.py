"""
Tables moduli sxemalari.

- TableCreate — yangi jadval
- TableUpdate — tahrirlash
- TableResponse — javob
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.config import settings
from backend.modules.styles.defaults import default_styles
from backend.modules.styles.schemas import normalize_styles


# ============================================
# JADVAL YARATISH — SO'ROV
# ============================================
class TableCreate(BaseModel):
    """
    Yangi jadval yaratish so'rovi.

    Misol:
        {
            "title": "Xodimlar",
            "columns": ["Ism", "Lavozim", "Maosh"],
            "rows": [["Ali", "Dasturchi", 5000]],
            "source": "ai"
        }
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Jadval sarlavhasi",
    )

    columns: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Ustunlar",
    )

    rows: list[list[Any]] = Field(
        ...,
        min_length=1,
        description="Qatorlar",
    )

    styles: dict = Field(
        default_factory=default_styles,
        description="Jadval uslublari",
    )

    source: str = Field(
        default="ai",
        pattern="^(ai|demo|manual|upload)$",
        description="Manba: 'ai', 'demo', 'manual', 'upload'",
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Jadval sarlavhasi bo'sh bo'lishi mumkin emas")
        return v

    @field_validator("columns")
    @classmethod
    def columns_valid(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Kamida bitta ustun bo'lishi kerak")

        cleaned = []
        for i, col in enumerate(v):
            col_clean = str(col).strip()
            if not col_clean:
                raise ValueError(f"{i + 1}-ustun bo'sh")
            cleaned.append(col_clean)

        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Ustun nomlari takrorlanmasligi kerak")

        return cleaned

    @field_validator("styles", mode="before")
    @classmethod
    def styles_valid(cls, value: dict | None) -> dict:
        return normalize_styles(value)

    @model_validator(mode="after")
    def validate_structure(self) -> "TableCreate":
        """Ustun-qator mosligini tekshirish."""
        n_cols = len(self.columns)
        n_rows = len(self.rows)

        if n_cols > settings.max_columns:
            raise ValueError(f"Ustunlar {settings.max_columns} tadan oshmasligi kerak")

        if n_rows > settings.max_rows:
            raise ValueError(f"Qatorlar {settings.max_rows} tadan oshmasligi kerak")

        for i, row in enumerate(self.rows):
            if len(row) != n_cols:
                raise ValueError(
                    f"{i + 1}-qatorda {len(row)} ta qiymat, "
                    f"lekin {n_cols} ta ustun kutilgan"
                )

        return self


# ============================================
# JADVALNI TAHRIRLASH — SO'ROV
# ============================================
class TableUpdate(BaseModel):
    """
    Jadvalni tahrirlash so'rovi.

    Faqat berilgan maydonlar yangilanadi.
    """

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    columns: Optional[list[str]] = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    rows: Optional[list[list[Any]]] = Field(
        default=None,
        min_length=1,
    )

    styles: Optional[dict] = None

    @field_validator("styles", mode="before")
    @classmethod
    def styles_valid(cls, value: dict | None) -> dict | None:
        if value is not None:
            normalize_styles(value)
        return value


# ============================================
# JADVAL — JAVOB
# ============================================
class TableResponse(BaseModel):
    """
    Jadval javobi.

    Misol:
        {
            "id": 1,
            "chat_id": 1,
            "title": "Xodimlar",
            "columns": ["Ism", "Lavozim"],
            "rows": [["Ali", "Dasturchi"]],
            "source": "ai",
            "version": 1,
            "row_count": 1,
            "column_count": 2,
            "has_formulas": false,
            "formula_count": 0,
            "created_at": "...",
            "updated_at": "..."
        }
    """

    id: int
    chat_id: int
    title: str
    columns: list[Any]
    rows: list[Any]
    styles: dict = Field(default_factory=default_styles)
    source: str
    version: int
    row_count: int
    column_count: int
    has_formulas: bool
    formula_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, table) -> "TableResponse":
        """SQLAlchemy modelidan javob yaratish."""
        return cls(
            id=table.id,
            chat_id=table.chat_id,
            title=table.title,
            columns=table.columns,
            rows=table.rows,
            styles=normalize_styles(table.styles),
            source=table.source,
            version=table.version,
            row_count=len(table.rows) if table.rows else 0,
            column_count=len(table.columns) if table.columns else 0,
            has_formulas=table.has_formulas(),
            formula_count=table.formula_count(),
            created_at=table.created_at,
            updated_at=table.updated_at,
        )