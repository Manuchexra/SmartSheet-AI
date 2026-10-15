"""
Message modeli.

Message — bu chatdagi bitta xabar.
- role: 'user', 'ai', yoki 'system'
- content: xabar matni
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, func, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from backend.db.base import Base


# TYPE_CHECKING — circular import oldini olish
if TYPE_CHECKING:
    from backend.models.chat import Chat


class MessageRole(str, enum.Enum):
    """Xabar rollari."""
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class Message(Base):
    """
    Message modeli.

    Misol:
        msg = Message(chat_id=1, role=MessageRole.USER, content="Xodimlar jadvali")
        db.add(msg)
        db.commit()
    """

    __tablename__ = "messages"

    # ============================================
    # USTUNLAR
    # ============================================
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ============================================
    # RELATIONSHIP'LAR
    # ============================================
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="messages",
    )

    # ============================================
    # INDEX'LAR
    # ============================================
    __table_args__ = (
        Index("ix_messages_chat_created", "chat_id", "created_at"),
    )

    # ============================================
    # YORDAMCHI METODLAR
    # ============================================
    def __repr__(self) -> str:
        preview = self.content[:30] if self.content else ""
        return f"<Message(id={self.id}, role='{self.role}', content='{preview}...')>"

    def to_dict(self) -> dict:
        """Message'ni dict'ga aylantirish."""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }