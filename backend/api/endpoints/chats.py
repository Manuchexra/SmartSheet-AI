"""
Chats endpointlari.

- POST   /api/v1/chats          — yangi chat
- GET    /api/v1/chats          — chatlar ro'yxati
- GET    /api/v1/chats/{id}     — bitta chat
- PATCH  /api/v1/chats/{id}     — tahrirlash
- DELETE /api/v1/chats/{id}     — o'chirish
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.modules.chats.schemas import (
    ChatCreate,
    ChatListResponse,
    ChatResponse,
    ChatUpdate,
)
from backend.modules.chats.service import (
    create_chat,
    delete_chat,
    get_chat,
    get_chats,
    update_chat,
)

from backend.modules.ai.schemas import AIError, AIRequest
from backend.modules.ai.service import (
    generate_edit_with_ai,
    generate_with_ai,
)
from backend.modules.chats.schemas import (
    ChatCreate,
    ChatGenerateRequest,
    ChatGenerateResponse,
    ChatListResponse,
    ChatResponse,
    ChatUpdate,
)
from backend.modules.messages.schemas import MessageResponse
from backend.modules.messages.service import create_message
from backend.modules.tables.schemas import TableResponse
from backend.modules.tables.service import get_table_by_chat, upsert_table

from backend.config import settings
from backend.modules.ai.schemas import (
    AIError,
    AIInvalidResponseError,
    AIRateLimitError,
    AIRequest,
    AITimeoutError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["Chats"])


# ============================================
# POST /api/v1/chats — YANGI CHAT
# ============================================
@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi chat yaratish",
    description="Yangi chat yaratadi va uni qaytaradi.",
)
def create_chat_endpoint(
    payload: ChatCreate,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Yangi chat yaratish."""
    try:
        chat = create_chat(db, title=payload.title)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return ChatResponse.from_model(chat)


# ============================================
# GET /api/v1/chats — CHATLAR RO'YXATI
# ============================================
@router.get(
    "",
    response_model=ChatListResponse,
    summary="Chatlar ro'yxati",
    description="Barcha chatlarni qaytaradi (yangilangan vaqt bo'yicha).",
)
def list_chats_endpoint(
    skip: int = Query(0, ge=0, description="O'tkazib yuborish"),
    limit: int = Query(50, ge=1, le=100, description="Limit"),
    db: Session = Depends(get_db),
) -> ChatListResponse:
    """Chatlar ro'yxatini olish."""
    chats, total = get_chats(db, skip=skip, limit=limit)

    return ChatListResponse(
        chats=[ChatResponse.from_model(c) for c in chats],
        total=total,
    )


# ============================================
# GET /api/v1/chats/{id} — BITTA CHAT
# ============================================
@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
    summary="Bitta chat",
    description="Chatni ID bo'yicha qaytaradi.",
)
def get_chat_endpoint(
    chat_id: int,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Bitta chatni olish."""
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )
    return ChatResponse.from_model(chat)


# ============================================
# PATCH /api/v1/chats/{id} — TAHRIRLASH
# ============================================
@router.patch(
    "/{chat_id}",
    response_model=ChatResponse,
    summary="Chatni tahrirlash",
    description="Chat sarlavhasini o'zgartiradi.",
)
def update_chat_endpoint(
    chat_id: int,
    payload: ChatUpdate,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Chatni tahrirlash."""
    chat = update_chat(db, chat_id, title=payload.title)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )
    return ChatResponse.from_model(chat)


# ============================================
# DELETE /api/v1/chats/{id} — O'CHIRISH
# ============================================
@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Chatni o'chirish",
    description="Chatni va unga tegishli barcha xabarlar va jadvalni o'chiradi.",
)
def delete_chat_endpoint(
    chat_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Chatni o'chirish."""
    deleted = delete_chat(db, chat_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )

# ============================================
# POST /api/v1/chats/{chat_id}/generate
# ============================================
@router.post(
    "/{chat_id}/generate",
    response_model=ChatGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="AI orqali jadval yaratish/tahrirlash",
    description=(
        "Chat ichida AI'ga so'rov yuboradi. "
        "Agar jadval mavjud bo'lsa — tahrirlaydi, "
        "aks holda — yangi yaratadi."
    ),
)
def chat_generate_endpoint(
    chat_id: int,
    payload: ChatGenerateRequest,
    db: Session = Depends(get_db),
) -> ChatGenerateResponse:
    """
    Chat ichida AI orqali jadval yaratish yoki tahrirlash.

    Oqim:
    1. Chat mavjudligini tekshirish
    2. Foydalanuvchi xabarini saqlash
    3. Mavjud jadvalni olish (agar bor bo'lsa)
    4. AI'ga so'rov yuborish
    5. Jadvalni upsert qilish
    6. AI xabarini saqlash
    7. Javob qaytarish
    """
    # 1. Chat mavjudligini tekshirish
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )

    # 2. Foydalanuvchi xabarini saqlash
    try:
        user_message = create_message(
            db,
            chat_id=chat_id,
            role="user",
            content=payload.prompt,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # 3. Mavjud jadvalni olish
    existing_table = get_table_by_chat(db, chat_id)

    # 4. AI'ga so'rov
    try:
        if existing_table:
            # EDIT rejimi
            logger.info(f"AI edit rejimi: chat_id={chat_id}")
            ai_response, source = generate_edit_with_ai(
                user_request=payload.prompt,
                existing_table={
                    "title": existing_table.title,
                    "columns": existing_table.columns,
                    "rows": existing_table.rows,
                },
            )
        else:
            # YANGI jadval
            logger.info(f"AI yaratish rejimi: chat_id={chat_id}")
            ai_request = AIRequest(
                prompt=payload.prompt,
                max_rows=settings.max_rows,
                max_columns=settings.max_columns,
            )
            ai_response, source = generate_with_ai(ai_request)
    except (AITimeoutError, AIRateLimitError, AIInvalidResponseError, AIError) as e:
        logger.warning(f"AI xatosi: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI xizmati xatosi: {e}",
        ) from e

    # 5. Jadvalni upsert qilish
    try:
        table = upsert_table(
            db,
            chat_id=chat_id,
            title=ai_response.title,
            columns=ai_response.columns,
            rows=ai_response.rows,
            source=source,
        )
    except ValueError as e:
        logger.error(f"Jadval saqlash xatosi: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Jadval saqlanmadi: {e}",
        ) from e

    if chat.title == "Yangi chat":
        chat = update_chat(db, chat_id, title=table.title)

    # 6. AI xabarini saqlash
    ai_content = f"Jadval yaratildi: {table.title} ({len(table.rows)} qator)"
    if existing_table:
        ai_content = f"Jadval tahrirlandi (version {table.version}): {table.title}"

    ai_message = create_message(
        db,
        chat_id=chat_id,
        role="ai",
        content=ai_content,
    )

    # 7. Javob
    return ChatGenerateResponse(
        user_message=MessageResponse.from_model(user_message),
        ai_message=MessageResponse.from_model(ai_message),
        chat=ChatResponse.from_model(chat),
        table=TableResponse.from_model(table),
    )