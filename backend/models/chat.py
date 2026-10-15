"""
Chat modeli.

Chat — bu foydalanuvchi va AI o'rtasidagi suhbat.
Har bir chatda:
- Sarlavha (title)
- Ko'p xabar (messages)
- Bitta jadval (table)
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


# TYPE_CHECKING — circular import oldini olish uchun
if TYPE_CHECKING:
    from backend.models.message import Message
    from backend.models.table import Table


class Chat(Base):
    """
    Chat modeli.

    Misol:
        chat = Chat(title="Xodimlar jadvali")
        db.add(chat)
        db.commit()
    """

    __tablename__ = "chats"

    # ============================================
    # USTUNLAR
    # ============================================
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="Yangi chat",
        index=True,  # Qidiruv uchun indeks
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ============================================
    # RELATIONSHIP'LAR
    # ============================================
    # Chat → Messages (1:N)
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",  # Chat o'chsa, xabarlar ham o'chadi
        order_by="Message.created_at",
        lazy="selectin",  # Avtomatik yuklash (N+1 muammosini oldini oladi)
    )

    # Chat → Table (1:1)
    table: Mapped[Optional["Table"]] = relationship(
        "Table",
        back_populates="chat",
        cascade="all, delete-orphan",  # Chat o'chsa, jadval ham o'chadi
        uselist=False,  # 1:1 uchun
        lazy="selectin",
    )

    # ============================================
    # INDEX'LAR
    # ============================================
    __table_args__ = (
        Index("ix_chats_updated_at", "updated_at"),
    )

    # ============================================
    # YORDAMCHI METODLAR
    # ============================================
    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, title='{self.title}')>"

    def to_dict(self) -> dict:
        """Chat'ni dict'ga aylantirish."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0,
            "has_table": self.table is not None,
        }