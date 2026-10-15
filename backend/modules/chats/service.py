"""
Chats moduli xizmati.

Bu modul Chat uchun CRUD funksiyalarini beradi:
- create_chat() — yangi chat
- get_chat() — bitta chat
- get_chats() — chatlar ro'yxati
- update_chat() — tahrirlash
- delete_chat() — o'chirish
"""

import logging

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Chat


logger = logging.getLogger(__name__)


# ============================================
# YANGI CHAT YARATISH
# ============================================
def create_chat(db: Session, title: str = "Yangi chat") -> Chat:
    """
    Yangi chat yaratish.

    Args:
        db: SQLAlchemy sessiyasi.
        title: Chat sarlavhasi.

    Returns:
        Chat — yaratilgan chat.

    Raises:
        ValueError: Chatlar limiti tugagan bo'lsa.
    """
    # Limitni tekshirish
    total = db.scalar(select(func.count()).select_from(Chat))
    if total >= settings.max_chats:
        raise ValueError(
            f"Chatlar limiti tugagan ({settings.max_chats}). "
            f"Iltimos, ba'zilarini o'chiring."
        )

    chat = Chat(title=title)
    db.add(chat)
    db.commit()
    db.refresh(chat)

    logger.info(f"✅ Yangi chat yaratildi: id={chat.id}, title='{chat.title}'")
    return chat


# ============================================
# BITTA CHATNI OLISH
# ============================================
def get_chat(db: Session, chat_id: int) -> Chat | None:
    """
    Chatni ID bo'yicha olish.

    Args:
        db: SQLAlchemy sessiyasi.
        chat_id: Chat ID.

    Returns:
        Chat yoki None (topilmasa).
    """
    return db.get(Chat, chat_id)


# ============================================
# CHATLAR RO'YXATI
# ============================================
def get_chats(
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Chat], int]:
    """
    Chatlar ro'yxatini olish.

    Args:
        db: SQLAlchemy sessiyasi.
        skip: Nechta o'tkazib yuborish.
        limit: Nechta olish.

    Returns:
        (chats, total) — chatlar ro'yxati va jami soni.
    """
    # Jami soni
    total = db.scalar(select(func.count()).select_from(Chat))

    # Chatlar (yangilangan vaqt bo'yicha teskari tartibda)
    stmt = (
        select(Chat)
        .order_by(desc(Chat.updated_at))
        .offset(skip)
        .limit(limit)
    )
    chats = list(db.scalars(stmt).all())

    return chats, total


# ============================================
# CHATNI TAHRIRLASH
# ============================================
def update_chat(
    db: Session,
    chat_id: int,
    title: str | None = None,
) -> Chat | None:
    """
    Chatni tahrirlash.

    Args:
        db: SQLAlchemy sessiyasi.
        chat_id: Chat ID.
        title: Yangi sarlavha (None bo'lsa, o'zgarmaydi).

    Returns:
        Chat yoki None (topilmasa).
    """
    chat = db.get(Chat, chat_id)
    if not chat:
        return None

    if title is not None:
        chat.title = title

    db.commit()
    db.refresh(chat)

    logger.info(f"✅ Chat tahrirlandi: id={chat.id}, title='{chat.title}'")
    return chat


# ============================================
# CHATNI O'CHIRISH
# ============================================
def delete_chat(db: Session, chat_id: int) -> bool:
    """
    Chatni o'chirish.

    Cascade tufayli barcha xabarlar va jadval ham o'chadi.

    Args:
        db: SQLAlchemy sessiyasi.
        chat_id: Chat ID.

    Returns:
        True — o'chirildi, False — topilmadi.
    """
    chat = db.get(Chat, chat_id)
    if not chat:
        return False

    db.delete(chat)
    db.commit()

    logger.info(f"🗑️  Chat o'chirildi: id={chat_id}")
    return True