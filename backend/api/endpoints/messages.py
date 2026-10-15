"""
Messages endpointlari.

- GET    /api/v1/chats/{chat_id}/messages        — xabarlar ro'yxati
- POST   /api/v1/chats/{chat_id}/messages        — yangi xabar
- DELETE /api/v1/chats/{chat_id}/messages/{id}   — xabarni o'chirish
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.modules.chats.service import get_chat
from backend.modules.messages.schemas import (
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)
from backend.modules.messages.service import (
    create_message,
    delete_message,
    get_messages,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["Messages"])


# ============================================
# GET /api/v1/chats/{chat_id}/messages — RO'YXAT
# ============================================
@router.get(
    "/{chat_id}/messages",
    response_model=MessageListResponse,
    summary="Xabarlar ro'yxati",
    description="Chatdagi barcha xabarlarni qaytaradi (vaqt bo'yicha).",
)
def list_messages_endpoint(
    chat_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> MessageListResponse:
    """Xabarlar ro'yxatini olish."""
    # Chat mavjudligini tekshirish
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )

    messages, total = get_messages(db, chat_id, skip=skip, limit=limit)

    return MessageListResponse(
        messages=[MessageResponse.from_model(m) for m in messages],
        total=total,
        chat_id=chat_id,
    )


# ============================================
# POST /api/v1/chats/{chat_id}/messages — YANGI
# ============================================
@router.post(
    "/{chat_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi xabar",
    description="Chatga yangi xabar qo'shadi.",
)
def create_message_endpoint(
    chat_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Yangi xabar yaratish."""
    try:
        message = create_message(
            db,
            chat_id=chat_id,
            role=payload.role,
            content=payload.content,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return MessageResponse.from_model(message)


# ============================================
# DELETE /api/v1/chats/{chat_id}/messages/{id}
# ============================================
@router.delete(
    "/{chat_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xabarni o'chirish",
    description="Xabarni ID bo'yicha o'chiradi.",
)
def delete_message_endpoint(
    chat_id: int,
    message_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Xabarni o'chirish."""
    # Chat mavjudligini tekshirish
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )

    deleted = delete_message(db, message_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Xabar topilmadi: id={message_id}",
        )