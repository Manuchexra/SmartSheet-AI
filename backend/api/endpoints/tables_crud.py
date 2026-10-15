"""
Tables CRUD endpointlari (chat ichida).

- GET    /api/v1/chats/{chat_id}/table        — jadvalni olish
- POST   /api/v1/chats/{chat_id}/table        — yangi jadval
- PUT    /api/v1/chats/{chat_id}/table        — yaratish yoki yangilash
- PATCH  /api/v1/chats/{chat_id}/table        — tahrirlash
- DELETE /api/v1/chats/{chat_id}/table        — o'chirish

Diqqat: /api/v1/tables/generate (AI) boshqa faylda.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.modules.chats.service import get_chat
from backend.modules.tables.schemas import (
    TableCreate,
    TableResponse,
    TableUpdate,
)
from backend.modules.tables.service import (
    create_table,
    delete_table,
    get_table_by_chat,
    update_table,
    upsert_table,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["Tables (CRUD)"])


# ============================================
# GET /api/v1/chats/{chat_id}/table
# ============================================
@router.get(
    "/{chat_id}/table",
    response_model=TableResponse,
    summary="Jadvalni olish",
    description="Chatdagi jadvalni qaytaradi.",
)
def get_table_endpoint(
    chat_id: int,
    db: Session = Depends(get_db),
) -> TableResponse:
    """Chatdagi jadvalni olish."""
    # Chat mavjudligini tekshirish
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )

    table = get_table_by_chat(db, chat_id)
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bu chatda jadval yo'q: chat_id={chat_id}",
        )

    return TableResponse.from_model(table)


# ============================================
# POST /api/v1/chats/{chat_id}/table
# ============================================
@router.post(
    "/{chat_id}/table",
    response_model=TableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi jadval",
    description="Chat uchun yangi jadval yaratadi.",
)
def create_table_endpoint(
    chat_id: int,
    payload: TableCreate,
    db: Session = Depends(get_db),
) -> TableResponse:
    """Yangi jadval yaratish."""
    try:
        table = create_table(
            db,
            chat_id=chat_id,
            title=payload.title,
            columns=payload.columns,
            rows=payload.rows,
            source=payload.source,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return TableResponse.from_model(table)


# ============================================
# PUT /api/v1/chats/{chat_id}/table — UPSERT
# ============================================
@router.put(
    "/{chat_id}/table",
    response_model=TableResponse,
    summary="Yaratish yoki yangilash",
    description="Agar jadval mavjud bo'lsa — yangilaydi, aks holda — yaratadi.",
)
def upsert_table_endpoint(
    chat_id: int,
    payload: TableCreate,
    db: Session = Depends(get_db),
) -> TableResponse:
    """Jadvalni yaratish yoki yangilash."""
    try:
        table = upsert_table(
            db,
            chat_id=chat_id,
            title=payload.title,
            columns=payload.columns,
            rows=payload.rows,
            source=payload.source,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return TableResponse.from_model(table)


# ============================================
# PATCH /api/v1/chats/{chat_id}/table
# ============================================
@router.patch(
    "/{chat_id}/table",
    response_model=TableResponse,
    summary="Jadvalni tahrirlash",
    description="Jadvalning berilgan qismlarini yangilaydi.",
)
def update_table_endpoint(
    chat_id: int,
    payload: TableUpdate,
    db: Session = Depends(get_db),
) -> TableResponse:
    """Jadvalni tahrirlash."""
    # Chat mavjudligini tekshirish
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )

    table = update_table(
        db,
        chat_id=chat_id,
        title=payload.title,
        columns=payload.columns,
        rows=payload.rows,
    )
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bu chatda jadval yo'q: chat_id={chat_id}",
        )

    return TableResponse.from_model(table)


# ============================================
# DELETE /api/v1/chats/{chat_id}/table
# ============================================
@router.delete(
    "/{chat_id}/table",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Jadvalni o'chirish",
    description="Chatdagi jadvalni o'chiradi.",
)
def delete_table_endpoint(
    chat_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Jadvalni o'chirish."""
    # Chat mavjudligini tekshirish
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )

    deleted = delete_table(db, chat_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bu chatda jadval yo'q: chat_id={chat_id}",
        )