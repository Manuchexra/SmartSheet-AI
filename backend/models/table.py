"""
Table modeli.

Table — bu chatga tegishli jadval.
- columns: JSON (ustunlar ro'yxati)
- rows: JSON (qatorlar)
- source: 'ai' yoki 'demo'
- version: versiya raqami (har tahrirda oshadi)
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, DateTime, ForeignKey, func, Integer, JSON, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


# TYPE_CHECKING — circular import oldini olish
if TYPE_CHECKING:
    from backend.models.chat import Chat


class Table(Base):
    """
    Table modeli.

    Misol:
        table = Table(
            chat_id=1,
            title="Xodimlar",
            columns=["Ism", "Lavozim", "Maosh"],
            rows=[["Ali", "Dasturchi", 5000]]
        )
        db.add(table)
        db.commit()
    """

    __tablename__ = "tables"

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
        unique=True,  # 1:1 — bir chatda bir jadval
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="Jadval",
    )

    columns: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    rows: Mapped[list[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    styles: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ai",
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
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
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="table",
    )

    # ============================================
    # INDEX'LAR
    # ============================================
    __table_args__ = (
        Index("ix_tables_updated_at", "updated_at"),
    )

    # ============================================
    # YORDAMCHI METODLAR
    # ============================================
    def __repr__(self) -> str:
        return f"<Table(id={self.id}, chat_id={self.chat_id}, title='{self.title}')>"

    def to_dict(self) -> dict:
        """Table'ni dict'ga aylantirish."""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "title": self.title,
            "columns": self.columns,
            "rows": self.rows,
            "styles": self.styles,
            "source": self.source,
            "version": self.version,
            "row_count": len(self.rows) if self.rows else 0,
            "column_count": len(self.columns) if self.columns else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # ============================================
    # FORMULA YORDAMCHILARI
    # ============================================
    def has_formulas(self) -> bool:
        """Jadvalda formulalar bormi?"""
        for row in self.rows or []:
            for cell in row:
                if isinstance(cell, str) and cell.startswith("=") and len(cell) > 1:
                    return True
        return False

    def formula_count(self) -> int:
        """Formulalar soni."""
        count = 0
        for row in self.rows or []:
            for cell in row:
                if isinstance(cell, str) and cell.startswith("=") and len(cell) > 1:
                    count += 1
        return count