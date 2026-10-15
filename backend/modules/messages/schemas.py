"""
Messages moduli sxemalari.

- MessageCreate — yangi xabar yaratish
- MessageResponse — xabar javobi
- MessageListResponse — xabarlar ro'yxati
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================
# XABAR YARATISH — SO'ROV
# ============================================
class MessageCreate(BaseModel):
    """
    Yangi xabar yaratish so'rovi.

    Misol:
        {"role": "user", "content": "5 ta xodim uchun jadval yarat"}
    """

    role: Literal["user", "ai", "system"] = Field(
        default="user",
        description="Xabar roli: 'user', 'ai' yoki 'system'",
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Xabar matni",
        examples=["5 ta xodim uchun jadval yarat"],
    )

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Xabar bo'sh bo'lmasligi kerak."""
        v = v.strip()
        if not v:
            raise ValueError("Xabar bo'sh bo'lishi mumkin emas")
        return v


# ============================================
# XABAR — JAVOB
# ============================================
class MessageResponse(BaseModel):
    """
    Xabar javobi.

    Misol:
        {
            "id": 1,
            "chat_id": 1,
            "role": "user",
            "content": "5 ta xodim uchun jadval yarat",
            "created_at": "2026-10-15T10:00:00"
        }
    """

    id: int = Field(..., description="Xabar ID")
    chat_id: int = Field(..., description="Chat ID")
    role: str = Field(..., description="Xabar roli")
    content: str = Field(..., description="Xabar matni")
    created_at: datetime = Field(..., description="Yaratilgan vaqt")

    @classmethod
    def from_model(cls, message) -> "MessageResponse":
        """SQLAlchemy modelidan javob yaratish."""
        return cls(
            id=message.id,
            chat_id=message.chat_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )


# ============================================
# XABARLAR RO'YXATI — JAVOB
# ============================================
class MessageListResponse(BaseModel):
    """
    Xabarlar ro'yxati.

    Misol:
        {
            "messages": [...],
            "total": 5,
            "chat_id": 1
        }
    """

    messages: list[MessageResponse] = Field(
        default_factory=list,
        description="Xabarlar ro'yxati",
    )
    total: int = Field(
        default=0,
        ge=0,
        description="Jami xabarlar soni",
    )
    chat_id: int = Field(..., description="Chat ID")