"""Default table style used by the API, AI, frontend, and Excel export."""

from backend.modules.styles.schemas import TableStyles


def default_styles() -> dict:
    """Return an independent copy of the default style."""
    return TableStyles().model_dump(mode="json", exclude_none=True)
