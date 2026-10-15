"""Read uploaded CSV and Excel files into the application's table format."""

import csv
from datetime import date, datetime
from io import BytesIO, StringIO
from pathlib import PurePosixPath
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from backend.config import settings
from backend.modules.styles.defaults import default_styles
from backend.modules.table_generator.schemas import TableData

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def read_uploaded_table(filename: str, content: bytes) -> dict:
    """Parse the first worksheet or CSV into a validated table dictionary."""
    if not content:
        raise ValueError("Yuklangan fayl bo'sh.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("Fayl hajmi 10 MB dan oshmasligi kerak.")

    suffix = PurePosixPath(filename.replace("\\", "/")).suffix.lower()
    if suffix == ".csv":
        title = PurePosixPath(filename.replace("\\", "/")).stem
        columns, rows = _read_csv(content)
        styles = default_styles()
    elif suffix == ".xlsx":
        title, columns, rows, styles = _read_xlsx(content)
    else:
        raise ValueError("Faqat .xlsx yoki .csv fayllarini yuklash mumkin.")

    title = (title.strip() or "Yuklangan jadval")[:200]
    table = TableData(title=title, columns=columns, rows=rows, styles=styles)
    return table.model_dump(mode="json")


def _read_csv(content: bytes) -> tuple[list[str], list[list[object]]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("CSV fayli UTF-8 kodlashida bo'lishi kerak.") from error

    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    parsed_rows = list(csv.reader(StringIO(text), dialect))
    return _normalize_rows(parsed_rows)


def _read_xlsx(content: bytes) -> tuple[str, list[str], list[list[object]], dict]:
    try:
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=False)
    except (BadZipFile, InvalidFileException, OSError) as error:
        raise ValueError("XLSX faylini o'qib bo'lmadi. Fayl buzilgan bo'lishi mumkin.") from error

    try:
        worksheet = workbook.active
        if worksheet is None:
            raise ValueError("XLSX faylida ishchi varaq topilmadi.")

        if worksheet.max_column > settings.max_columns:
            raise ValueError(
                f"Jadval {settings.max_columns} tadan ko'p ustunli bo'lmasligi kerak."
            )
        if worksheet.max_row > settings.max_rows + 1:
            raise ValueError(
                f"Jadval sarlavhadan tashqari {settings.max_rows} qatordan oshmasligi kerak."
            )

        parsed_rows = []
        cell_styles = {}
        for row_index, row in enumerate(worksheet.iter_rows(values_only=False)):
            parsed_rows.append([_json_value(cell.value) for cell in row])
            for column_index, cell in enumerate(row):
                if cell.has_style:
                    style = _cell_style(cell)
                    if style:
                        cell_styles[f"{row_index}:{column_index}"] = style
        columns, rows = _normalize_rows(parsed_rows)
        styles = default_styles()
        styles["cells"] = cell_styles
        return worksheet.title, columns, rows, styles
    except (BadZipFile, InvalidFileException, OSError, KeyError, ParseError) as error:
        raise ValueError("XLSX faylini o'qib bo'lmadi. Fayl buzilgan bo'lishi mumkin.") from error
    finally:
        workbook.close()


def _normalize_rows(parsed_rows: list[list[object]]) -> tuple[list[str], list[list[object]]]:
    while parsed_rows and not any(value not in (None, "") for value in parsed_rows[-1]):
        parsed_rows.pop()
    if len(parsed_rows) < 2:
        raise ValueError("Jadvalda sarlavha va kamida bitta ma'lumot qatori bo'lishi kerak.")

    header = parsed_rows[0]
    while header and header[-1] in (None, ""):
        header.pop()
    if not header:
        raise ValueError("Jadval sarlavhalari topilmadi.")
    if len(header) > settings.max_columns:
        raise ValueError(f"Jadval {settings.max_columns} tadan ko'p ustunli bo'lmasligi kerak.")

    columns = [str(value).strip() if value is not None else "" for value in header]
    if any(not column for column in columns):
        raise ValueError("Har bir ustun sarlavhasi to'ldirilgan bo'lishi kerak.")
    if len(columns) != len(set(columns)):
        raise ValueError("Ustun sarlavhalari takrorlanmasligi kerak.")

    rows = []
    for row_index, source_row in enumerate(parsed_rows[1:], start=2):
        if any(value not in (None, "") for value in source_row[len(columns):]):
            raise ValueError(
                f"{row_index}-qatorda sarlavhasiz qo'shimcha qiymatlar bor."
            )
        row = source_row[:len(columns)]
        row.extend([None] * (len(columns) - len(row)))
        rows.append(row)

    if len(rows) > settings.max_rows:
        raise ValueError(f"Jadval {settings.max_rows} tadan ko'p qatorli bo'lmasligi kerak.")
    return columns, rows


def _json_value(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _cell_style(cell) -> dict:
    """Preserve supported per-cell XLSX formatting in the HTML/Excel views."""
    style = {}
    if cell.fill.fill_type == "solid":
        color = _rgb_color(cell.fill.fgColor)
        if color:
            style["bg_color"] = color

    font = cell.font
    text_color = _rgb_color(font.color)
    if text_color:
        style["text_color"] = text_color
    if font.bold:
        style["bold"] = True
    if font.italic:
        style["italic"] = True
    if font.sz and float(font.sz).is_integer():
        style["font_size"] = int(font.sz)
    if font.name and font.name != "Calibri":
        style["font_family"] = font.name

    if cell.alignment.horizontal in ("left", "center", "right"):
        style["alignment"] = cell.alignment.horizontal
    if cell.alignment.vertical in ("top", "center", "bottom"):
        style["vertical_alignment"] = cell.alignment.vertical

    borders = {
        side_name: getattr(cell.border, side_name)
        for side_name in ("top", "bottom", "left", "right")
    }
    styled_borders = {
        name: side for name, side in borders.items() if side.style in (
            "hair", "thin", "medium", "thick", "double"
        )
    }
    border_styles = {side.style for side in styled_borders.values()}
    border_colors = {_rgb_color(side.color) for side in styled_borders.values()}
    if styled_borders and len(border_styles) == 1 and len(border_colors) == 1:
        style["border_style"] = next(iter(border_styles))
        border_color = next(iter(border_colors))
        if border_color:
            style["border_color"] = border_color
        style["border_sides"] = list(styled_borders)
    return style


def _rgb_color(color) -> str | None:
    if color is None or color.type != "rgb" or not color.rgb:
        return None
    value = str(color.rgb)
    if len(value) not in (6, 8):
        return None
    if len(value) == 8:
        if value[:2] == "00":
            return None
        value = value[-6:]
    return f"#{value.upper()}"
