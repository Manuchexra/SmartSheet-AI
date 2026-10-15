"""Dependencies shared by browser-scoped chat endpoints."""

from uuid import UUID

from fastapi import Header


def get_browser_id(x_client_id: UUID = Header(alias="X-Client-ID")) -> str:
    """Validate and normalize the browser's persistent client identifier."""
    return str(x_client_id)
