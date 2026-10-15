"""
AI modulining sxemalari.

Bu modul:
1. AI'ga yuboriladigan so'rov (AIRequest)
2. AI'dan keladigan javob (AIResponse)
3. AI xatolari (AIError va boshqalar)
"""

from pydantic import BaseModel, Field

from backend.modules.styles.schemas import TableStyles


# ============================================
# AI'GA SO'ROV
# ============================================
class AIRequest(BaseModel):
    """AI provayderiga yuboriladigan so'rov."""

    prompt: str = Field(
        ...,
        min_length=3,
        description="Foydalanuvchining tabiiy tildagi so'rovi",
    )

    max_rows: int = Field(
        default=200,
        ge=1,
        le=200,
        description="Maksimal qatorlar soni",
    )

    max_columns: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maksimal ustunlar soni",
    )


# ============================================
# AI'DAN JAVOB (xom)
# ============================================
class AIResponse(BaseModel):
    """AI provayderidan keladigan xom javob."""

    title: str = Field(..., description="Jadval nomi")
    columns: list[str] = Field(..., min_length=1, description="Ustunlar")
    rows: list[list] = Field(..., min_length=1, description="Qatorlar")
    styles: TableStyles = Field(default_factory=TableStyles, description="Jadval uslublari")


# ============================================
# AI XATOLARI
# ============================================
class AIError(Exception):
    """AI xatolari uchun asosiy exception."""

    def __init__(self, message: str, code: str = "ai_error"):
        super().__init__(message)
        self.code = code


class AITimeoutError(AIError):
    """AI timeout xatosi."""

    def __init__(self, message: str = "AI xizmati javob bermadi"):
        super().__init__(message, code="timeout")


class AIRateLimitError(AIError):
    """AI rate limit xatosi."""

    def __init__(self, message: str = "AI so'rovlar limiti tugadi"):
        super().__init__(message, code="rate_limit")


class AIInvalidResponseError(AIError):
    """AI noto'g'ri javob qaytardi."""

    def __init__(self, message: str = "AI noto'g'ri javob qaytardi"):
        super().__init__(message, code="invalid_response")