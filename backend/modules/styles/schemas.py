"""Validated spreadsheet style schemas."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Alignment = Literal["left", "center", "right"]
VerticalAlignment = Literal["top", "center", "bottom"]
BorderStyle = Literal["none", "hair", "thin", "medium", "thick", "double"]
BorderSide = Literal["top", "bottom", "left", "right"]


class StyleRule(BaseModel):
    """Optional style overrides for a header, row, or column."""

    model_config = ConfigDict(extra="forbid")

    bg_color: str | None = None
    text_color: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    font_size: int | None = Field(default=None, ge=8, le=72)
    font_family: str | None = Field(default=None, min_length=1, max_length=64)
    alignment: Alignment | None = None
    vertical_alignment: VerticalAlignment | None = None
    border_style: BorderStyle | None = None
    border_color: str | None = None
    border_sides: list[BorderSide] | None = None

    @field_validator("bg_color", "text_color", "border_color")
    @classmethod
    def validate_hex_color(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError("Rang #RRGGBB formatida bo'lishi kerak")
        return value.upper() if value else value

    @field_validator("font_family")
    @classmethod
    def validate_font_family(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[A-Za-z0-9 _,.-]+", value):
            raise ValueError("Shrift nomida ruxsat etilmagan belgilar bor")
        return value

    @field_validator("border_sides")
    @classmethod
    def unique_border_sides(cls, value: list[BorderSide] | None) -> list[BorderSide] | None:
        if value is not None and len(value) != len(set(value)):
            raise ValueError("Chegara tomonlari takrorlanmasligi kerak")
        return value


class HeaderStyle(StyleRule):
    bg_color: str = "#2563EB"
    text_color: str = "#FFFFFF"
    bold: bool = True
    font_size: int = Field(default=12, ge=8, le=72)
    alignment: Alignment = "center"


class BodyStyle(StyleRule):
    border_style: BorderStyle = "thin"
    border_color: str = "#000000"
    border_sides: list[BorderSide] = ["top", "bottom", "left", "right"]


class TableStyles(BaseModel):
    """Persisted style shape for a table."""

    model_config = ConfigDict(extra="forbid")

    header: HeaderStyle = Field(default_factory=HeaderStyle)
    body: BodyStyle = Field(default_factory=BodyStyle)
    columns: dict[str, StyleRule] = Field(default_factory=dict)
    rows: dict[str, StyleRule] = Field(default_factory=dict)
    cells: dict[str, StyleRule] = Field(default_factory=dict)
    alternate_rows: bool = False

    @field_validator("rows")
    @classmethod
    def validate_row_keys(cls, value: dict[str, StyleRule]) -> dict[str, StyleRule]:
        if any(not key.isdecimal() for key in value):
            raise ValueError("Qator uslubi indeksi 0 dan boshlangan butun son bo'lishi kerak")
        return value

    @field_validator("cells")
    @classmethod
    def validate_cell_keys(cls, value: dict[str, StyleRule]) -> dict[str, StyleRule]:
        if len(value) > 2100 or any(
            not re.fullmatch(r"\d+:\d+", key) for key in value
        ):
            raise ValueError("Katak uslubi kaliti 'qator:ustun' formatida bo'lishi kerak")
        return value


def normalize_styles(styles: dict | TableStyles | None) -> dict:
    """Validate partial style input and fill unspecified options with defaults."""
    if isinstance(styles, TableStyles):
        parsed = styles
    else:
        parsed = TableStyles.model_validate(styles or {})
    return parsed.model_dump(mode="json", exclude_none=True)


def merge_style_overrides(existing: dict | None, overrides: dict | None) -> dict:
    """Apply partial style changes without resetting unrelated settings."""
    merged = normalize_styles(existing)

    def apply_overrides(target: dict, changes: dict) -> None:
        for key, value in changes.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                apply_overrides(target[key], value)
            else:
                target[key] = value

    apply_overrides(merged, overrides or {})
    return normalize_styles(merged)
