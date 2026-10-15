"""
Chats moduli sxemalari.

Bu modul Chat uchun so'rov va javob tuzilmalarini belgilaydi:
- ChatCreate — yangi chat yaratish so'rovi
- ChatUpdate — chatni tahrirlash so'rovi
- ChatResponse — chat javobi
- ChatListResponse — chatlar ro'yxati
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.config import settings


# ============================================
# CHAT YARATISH — SO'ROV
# ============================================
class ChatCreate(BaseModel):
    """
    Yangi chat yaratish so'rovi.

    Misol:
        {"title": "Xodimlar jadvali"}
    """

    title: str = Field(
        default="Yangi chat",
        min_length=1,
        max_length=200,
        description="Chat sarlavhasi",
        examples=["Xodimlar jadvali"],
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Sarlavha bo'sh bo'lmasligi kerak."""
        v = v.strip()
        if not v:
            raise ValueError("Chat sarlavhasi bo'sh bo'lishi mumkin emas")
        return v


# ============================================
# CHATNI TAHRIRLASH — SO'ROV
# ============================================
class ChatUpdate(BaseModel):
    """
    Chatni tahrirlash so'rovi.

    Faqat `title` ni o'zgartirish mumkin.

    Misol:
        {"title": "Yangi nom"}
    """

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Yangi sarlavha",
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Agar title berilgan bo'lsa, bo'sh bo'lmasligi kerak."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("Chat sarlavhasi bo'sh bo'lishi mumkin emas")
        return v


# ============================================
# CHAT — JAVOB
# ============================================
class ChatResponse(BaseModel):
    """
    Chat javobi.

    Misol:
        {
            "id": 1,
            "title": "Xodimlar jadvali",
            "created_at": "2026-10-15T10:00:00",
            "updated_at": "2026-10-15T10:00:00",
            "message_count": 3,
            "has_table": true
        }
    """

    id: int = Field(..., description="Chat ID")
    title: str = Field(..., description="Chat sarlavhasi")
    created_at: datetime = Field(..., description="Yaratilgan vaqt")
    updated_at: datetime = Field(..., description="Yangilangan vaqt")
    message_count: int = Field(
        default=0,
        ge=0,
        description="Xabarlar soni",
    )
    has_table: bool = Field(
        default=False,
        description="Jadval mavjudmi?",
    )

    @classmethod
    def from_model(cls, chat) -> "ChatResponse":
        """SQLAlchemy modelidan javob yaratish."""
        return cls(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            message_count=len(chat.messages) if chat.messages else 0,
            has_table=chat.table is not None,
        )


# ============================================
# CHATLAR RO'YXATI — JAVOB
# ============================================
class ChatListResponse(BaseModel):
    """
    Chatlar ro'yxati javobi.

    Misol:
        {
            "chats": [...],
            "total": 5
        }
    """

    chats: list[ChatResponse] = Field(
        default_factory=list,
        description="Chatlar ro'yxati",
    )
    total: int = Field(
        default=0,
        ge=0,
        description="Jami chatlar soni",
    )


# ============================================
# CHAT GENERATE (12.7-bosqich)
# ============================================
from backend.modules.messages.schemas import MessageResponse
from backend.modules.tables.schemas import TableResponse


class ChatGenerateRequest(BaseModel):
    """
    Chat ichida AI'ga so'rov.

    Misol:
        {"prompt": "5 ta xodim uchun jadval yarat"}
        {"prompt": "Maoshni 10% oshir"}
    """

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Foydalanuvchi so'rovi",
    )

    @field_validator("prompt")
    @classmethod
    def prompt_must_be_understandable(cls, value: str) -> str:
        """Aniq ma'noli unlisiz bitta so'zdan jadval yaratmaslik."""
        prompt = value.strip()
        vowels = "aeiouyáéíóúàèìòùäëïöüаеёиоуыэюяўәөү"
        if (
            len(prompt) >= 4
            and prompt.isalpha()
            and not any(char.casefold() in vowels for char in prompt)
        ):
            raise ValueError(
                "So'rov tushunarsiz ko'rinadi. Qanday jadval kerakligini "
                "aniqroq yozing."
            )
        return prompt


class ChatGenerateResponse(BaseModel):
    """
    Chat generate javobi.

    Qaytaradi:
    - user_message: foydalanuvchi xabari
    - ai_message: AI javobi
    - chat: yangilangan chat
    - table: yangilangan jadval
    """

    user_message: MessageResponse = Field(..., description="Foydalanuvchi xabari")
    ai_message: MessageResponse = Field(..., description="AI javobi")
    chat: ChatResponse = Field(..., description="Yangilangan chat")
    table: TableResponse = Field(..., description="Jadval")