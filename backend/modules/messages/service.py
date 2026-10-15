"""
Messages moduli xizmati.

Bu modul xabarlar bilan ishlaydi:
- create_message() — yangi xabar
- get_message() — bitta xabar
- get_messages() — chatdagi xabarlar
- delete_message() — xabarni o'chirish
- delete_all_messages() — barcha xabarlarni o'chirish
"""

import logging

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Message, Chat


logger = logging.getLogger(__name__)


# ============================================
# YANGI XABAR YARATISH
# ============================================
def create_message(
    db: Session,
    chat_id: int,
    role: str,
    content: str,
) -> Message:
    """
    Yangi xabar yaratish.

    Args:
        db: SQLAlchemy sessiyasi.
        chat_id: Chat ID.
        role: 'user', 'ai' yoki 'system'.
        content: Xabar matni.

    Returns:
        Message — yaratilgan xabar.

    Raises:
        ValueError: Chat topilmasa yoki limit tugagan bo'lsa.
    """
    # Chat mavjudligini tekshirish
    chat = db.get(Chat, chat_id)
    if not chat:
        raise ValueError(f"Chat topilmadi: id={chat_id}")

    # Limitni tekshirish
    total = db.scalar(
        select(func.count())
        .select_from(Message)
        .where(Message.chat_id == chat_id)
    )
    if total >= settings.max_messages_per_chat:
        raise ValueError(
            f"Xabarlar limiti tugagan ({settings.max_messages_per_chat}). "
            f"Iltimos, yangi chat yarating."
        )

    message = Message(
        chat_id=chat_id,
        role=role,
        content=content,
    )
    db.add(message)

    # Chat'ning updated_at ni yangilash
    chat.updated_at = func.now()

    db.commit()
    db.refresh(message)

    logger.info(
        f"✅ Yangi xabar: id={message.id}, chat_id={chat_id}, role='{role}'"
    )
    return message


# ============================================
# BITTA XABARNI OLISH
# ============================================
def get_message(db: Session, message_id: int) -> Message | None:
    """Xabarni ID bo'yicha olish."""
    return db.get(Message, message_id)


# ============================================
# CHATDAGI XABARLAR
# ============================================
def get_messages(
    db: Session,
    chat_id: int,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Message], int]:
    """
    Chatdagi xabarlar ro'yxatini olish.

    Args:
        db: SQLAlchemy sessiyasi.
        chat_id: Chat ID.
        skip: Nechta o'tkazib yuborish.
        limit: Nechta olish.

    Returns:
        (messages, total) — xabarlar va jami soni.
    """
    # Jami soni
    total = db.scalar(
        select(func.count())
        .select_from(Message)
        .where(Message.chat_id == chat_id)
    )

    # Xabarlar (vaqt bo'yicha)
    stmt = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at)
        .offset(skip)
        .limit(limit)
    )
    messages = list(db.scalars(stmt).all())

    return messages, total


# ============================================
# XABARNI O'CHIRISH
# ============================================
def delete_message(db: Session, chat_id: int, message_id: int) -> bool:
    """Delete a message only when it belongs to the specified chat."""
    message = db.scalar(
        select(Message).where(
            Message.id == message_id,
            Message.chat_id == chat_id,
        )
    )
    if message is None:
        return False

    db.delete(message)
    db.commit()

    logger.info(f"🗑️  Xabar o'chirildi: id={message_id}")
    return True


# ============================================
# BARCHA XABARLARNI O'CHIRISH
# ============================================
def delete_all_messages(db: Session, chat_id: int) -> int:
    """
    Chatdagi barcha xabarlarni o'chirish.

    Returns:
        Nechta o'chirildi.
    """
    stmt = select(Message).where(Message.chat_id == chat_id)
    messages = list(db.scalars(stmt).all())

    count = len(messages)
    for msg in messages:
        db.delete(msg)

    db.commit()

    logger.info(f"🗑️  {count} ta xabar o'chirildi (chat_id={chat_id})")
    return count