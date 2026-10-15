"""
Table Generator modulining sxemalari.

Bu modul jadvalning asosiy tuzilmasini belgilaydi:
- TableData — to'liq jadval (title, columns, rows, styles)
- TableGenerateRequest — foydalanuvchi so'rovi (prompt)
- TableGenerateResponse — API javobi (jadval + metadata)
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.config import settings
from backend.modules.styles.defaults import default_styles
from backend.modules.styles.schemas import normalize_styles


class TableData(BaseModel):
    """Jadval ma'lumotlari, AI, Excel va API qatlamlarida birgalikda ishlatiladi."""

    title: str = Field(..., min_length=1, max_length=200, description="Jadval nomi")
    columns: list[str] = Field(..., min_length=1, max_length=20, description="Ustun sarlavhalari")
    rows: list[list[Any]] = Field(..., description="Jadval qatorlari")
    styles: dict = Field(default_factory=default_styles, description="Jadval uslublari")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Jadval nomi bo'sh bo'lishi mumkin emas")
        return value

    @field_validator("columns")
    @classmethod
    def columns_not_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("Kamida bitta ustun bo'lishi kerak")
        cleaned = [str(column).strip() for column in value]
        if any(not column for column in cleaned):
            raise ValueError("Ustun nomi bo'sh bo'lishi mumkin emas")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Ustun nomlari takrorlanmasligi kerak")
        return cleaned

    @field_validator("rows")
    @classmethod
    def rows_not_empty(cls, value: list[list[Any]]) -> list[list[Any]]:
        if not value:
            raise ValueError("Kamida bitta qator bo'lishi kerak")
        return value

    @field_validator("styles", mode="before")
    @classmethod
    def styles_valid(cls, value: dict | None) -> dict:
        return normalize_styles(value)

    @model_validator(mode="after")
    def validate_structure(self) -> "TableData":
        n_cols = len(self.columns)
        n_rows = len(self.rows)
        if n_cols > settings.max_columns:
            raise ValueError(
                f"Ustunlar soni {settings.max_columns} tadan oshmasligi kerak (hozir: {n_cols})"
            )
        if n_rows > settings.max_rows:
            raise ValueError(
                f"Qatorlar soni {settings.max_rows} tadan oshmasligi kerak (hozir: {n_rows})"
            )
        for i, row in enumerate(self.rows):
            if len(row) != n_cols:
                raise ValueError(
                    f"{i + 1}-qatorda {len(row)} ta qiymat bor, "
                    f"lekin {n_cols} ta ustun kutilgan"
                )
        return self

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.columns)


class TableGenerateRequest(BaseModel):
    """Foydalanuvchidan keladigan jadval yaratish so'rovi."""

    prompt: str = Field(..., min_length=3, max_length=2000, description="Foydalanuvchi so'rovi")

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Prompt bo'sh bo'lishi mumkin emas")
        if len(value) > settings.max_prompt_length:
            raise ValueError(
                f"Prompt {settings.max_prompt_length} belgidan oshmasligi kerak "
                f"(hozir: {len(value)})"
            )
        return value


class TableGenerateResponse(BaseModel):
    """Jadval yaratish endpointining javobi."""

    title: str = Field(..., description="Jadval nomi")
    columns: list[str] = Field(..., description="Ustun sarlavhalari")
    rows: list[list[Any]] = Field(..., description="Jadval qatorlari")
    styles: dict = Field(default_factory=default_styles, description="Jadval uslublari")
    row_count: int = Field(..., ge=0, description="Qatorlar soni")
    column_count: int = Field(..., ge=1, description="Ustunlar soni")
    source: str = Field(..., description="Jadval manbasi", pattern="^(ai|demo)$")

    @classmethod
    def from_table_data(cls, data: TableData, source: str) -> "TableGenerateResponse":
        return cls(
            title=data.title,
            columns=data.columns,
            rows=data.rows,
            styles=data.styles,
            row_count=data.row_count,
            column_count=data.column_count,
            source=source,
        )
