"""
Tables moduli xizmati.

Bu modul jadval bilan ishlaydi:
- create_table() — yangi jadval
- get_table() — jadvalni olish
- get_table_by_chat() — chat bo'yicha
- update_table() — tahrirlash
- upsert_table() — yaratish yoki yangilash
- delete_table() — o'chirish
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Table, Chat


logger = logging.getLogger(__name__)


# ============================================
# YANGI JADVAL YARATISH
# ============================================
def create_table(
    db: Session,
    chat_id: int,
    title: str,
    columns: list,
    rows: list,
    source: str = "ai",
) -> Table:
    """
    Yangi jadval yaratish.

    Raises:
        ValueError: Chat topilmasa yoki jadval allaqachon mavjud bo'lsa.
    """
    # Chat mavjudligini tekshirish
    chat = db.get(Chat, chat_id)
    if not chat:
        raise ValueError(f"Chat topilmadi: id={chat_id}")

    # Bu chatda jadval bormi?
    existing = db.scalar(
        select(Table).where(Table.chat_id == chat_id)
    )
    if existing:
        raise ValueError(
            f"Bu chatda allaqachon jadval mavjud (chat_id={chat_id}). "
            f"Yangilash uchun PATCH dan foydalaning."
        )

    table = Table(
        chat_id=chat_id,
        title=title,
        columns=columns,
        rows=rows,
        source=source,
        version=1,
    )
    db.add(table)
    db.commit()
    db.refresh(table)

    logger.info(
        f"✅ Yangi jadval: id={table.id}, chat_id={chat_id}, "
        f"{len(rows)} qator × {len(columns)} ustun"
    )
    return table


# ============================================
# JADVALNI OLISH
# ============================================
def get_table(db: Session, table_id: int) -> Table | None:
    """Jadvalni ID bo'yicha olish."""
    return db.get(Table, table_id)


def get_table_by_chat(db: Session, chat_id: int) -> Table | None:
    """Chatdagi jadvalni olish (1:1)."""
    return db.scalar(
        select(Table).where(Table.chat_id == chat_id)
    )


# ============================================
# JADVALNI TAHRIRLASH
# ============================================
def update_table(
    db: Session,
    chat_id: int,
    title: str | None = None,
    columns: list | None = None,
    rows: list | None = None,
) -> Table | None:
    """
    Jadvalni tahrirlash.

    Version har safar oshadi.

    Returns:
        Table yoki None (topilmasa).
    """
    table = get_table_by_chat(db, chat_id)
    if not table:
        return None

    if title is not None:
        table.title = title
    if columns is not None:
        table.columns = columns
    if rows is not None:
        table.rows = rows

    # Versiyani oshirish
    table.version += 1

    db.commit()
    db.refresh(table)

    logger.info(
        f"✅ Jadval tahrirlandi: id={table.id}, version={table.version}"
    )
    return table


# ============================================
# UPSERT — YARATISH YOKI YANGILASH
# ============================================
def upsert_table(
    db: Session,
    chat_id: int,
    title: str,
    columns: list,
    rows: list,
    source: str = "ai",
) -> Table:
    """
    Yaratish yoki yangilash.

    Bu — AI natijasini saqlash uchun eng qulay usul.
    """
    existing = get_table_by_chat(db, chat_id)

    if existing:
        return update_table(
            db,
            chat_id=chat_id,
            title=title,
            columns=columns,
            rows=rows,
        )

    return create_table(
        db,
        chat_id=chat_id,
        title=title,
        columns=columns,
        rows=rows,
        source=source,
    )


# ============================================
# JADVALNI O'CHIRISH
# ============================================
def delete_table(db: Session, chat_id: int) -> bool:
    """Chatdagi jadvalni o'chirish."""
    table = get_table_by_chat(db, chat_id)
    if not table:
        return False

    db.delete(table)
    db.commit()

    logger.info(f"🗑️  Jadval o'chirildi: chat_id={chat_id}")
    return True