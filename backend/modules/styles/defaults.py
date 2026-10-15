"""Default table style used by the API, AI, frontend, and Excel export."""

DEFAULT_STYLES = {
    "header": {
        "bg_color": "#2563EB",
        "text_color": "#FFFFFF",
        "bold": True,
        "font_size": 12,
        "alignment": "center",
    },
    "body": {
        "border_style": "thin",
        "border_color": "#000000",
        "border_sides": ["top", "bottom", "left", "right"],
    },
    "columns": {},
    "rows": {},
    "alternate_rows": False,
}


def default_styles() -> dict:
    """Return an independent copy of the default style."""
    return {
        **DEFAULT_STYLES,
        "header": dict(DEFAULT_STYLES["header"]),
        "body": {**DEFAULT_STYLES["body"], "border_sides": list(DEFAULT_STYLES["body"]["border_sides"])},
        "columns": {},
        "rows": {},
    }
