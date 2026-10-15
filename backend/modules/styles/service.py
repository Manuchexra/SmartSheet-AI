"""Style request helpers used by the no-provider demo edit path."""

import re

from backend.modules.styles.schemas import normalize_styles


COLOR_NAMES = {
    "ko'k": "#2563EB",
    "kok": "#2563EB",
    "blue": "#2563EB",
    "yashil": "#16A34A",
    "green": "#16A34A",
    "qizil": "#DC2626",
    "red": "#DC2626",
    "sariq": "#EAB308",
    "yellow": "#EAB308",
    "qora": "#000000",
    "black": "#000000",
    "oq": "#FFFFFF",
    "white": "#FFFFFF",
}


def apply_style_request(
    request: str,
    columns: list[str],
    current_styles: dict | None,
) -> dict | None:
    """Apply a directly supported style request consistently across AI modes."""
    text = request.lower()
    if not any(
        re.search(pattern, text)
        for pattern in (
            r"\bqil(?:ing|in|sin)?\b",
            r"\bbo'ya(?:ng|sin)?\b",
            r"\bmake\b",
            r"\bset\b",
            r"\bchange\b",
            r"\brang(?:ini)?\b",
            r"\bfon\b",
            r"\bchegara\b",
            r"\bborder\b",
            r"\bstyle\b",
            r"\bshrift\b",
            r"\bfont\b",
            r"\btekisla\b",
            r"\balignment\b",
        )
    ):
        return None

    normalized = normalize_styles(current_styles)
    color = next(
        (value for name, value in COLOR_NAMES.items() if re.search(rf"\b{re.escape(name)}\b", text)),
        None,
    )

    target_column = next(
        (column for column in columns if column.lower() in text),
        None,
    )
    is_first_row = bool(
        re.search(r"\b1\s*[- ]?\s*qator\b|\bbirinchi\s+qator\b", text)
    )
    is_header = is_first_row or any(
        word in text for word in ("sarlavha", "header", "sarlavhani")
    )
    is_border = any(word in text for word in ("chegara", "border"))
    is_alignment = any(word in text for word in ("tekisla", "alignment", "markazga", "chapga", "o'ngga"))
    is_font = any(word in text for word in ("shrift", "font", "matn"))

    if is_border:
        if any(word in text for word in ("qalin", "thick", "bold")):
            normalized["body"]["border_style"] = "thick"
        elif any(word in text for word in ("ingichka", "thin")):
            normalized["body"]["border_style"] = "thin"
        if color:
            normalized["body"]["border_color"] = color
        return normalized

    if is_alignment:
        alignment = next(
            (
                value
                for words, value in (
                    (("markaz", "center"), "center"),
                    (("chap", "left"), "left"),
                    (("o'ng", "right"), "right"),
                )
                if any(word in text for word in words)
            ),
            None,
        )
        if alignment:
            target = normalized["header"] if is_header else (
                normalized["columns"].setdefault(target_column, {}) if target_column else normalized["body"]
            )
            target["alignment"] = alignment
            return normalized

    if color:
        if is_header:
            normalized["header"]["text_color" if is_font else "bg_color"] = color
        elif target_column:
            column_style = normalized["columns"].setdefault(target_column, {})
            column_style["text_color" if is_font else "bg_color"] = color
        elif is_font:
            normalized["body"]["text_color"] = color
        else:
            normalized["header"]["bg_color"] = color
        return normalized

    if any(word in text for word in ("qalin", "bold")):
        target = normalized["header"] if is_header else (
            normalized["columns"].setdefault(target_column, {}) if target_column else None
        )
        if target is not None:
            target["bold"] = True
            return normalized

    return None
