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

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.modules.chats.dependencies import get_browser_id
from backend.modules.chats.service import get_chat, update_chat
from backend.modules.messages.service import create_message
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
from backend.modules.tables.importer import MAX_UPLOAD_BYTES, read_uploaded_table


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["Tables (CRUD)"])


def _require_chat(db: Session, chat_id: int, browser_id: str):
    chat = get_chat(db, chat_id, browser_id)
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat topilmadi: id={chat_id}",
        )
    return chat


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
    browser_id: str = Depends(get_browser_id),
    db: Session = Depends(get_db),
) -> TableResponse:
    """Chatdagi jadvalni olish."""
    _require_chat(db, chat_id, browser_id)

    table = get_table_by_chat(db, chat_id)
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bu chatda jadval yo'q: chat_id={chat_id}",
        )

    return TableResponse.from_model(table)


@router.post(
    "/{chat_id}/table/upload",
    response_model=TableResponse,
    summary="Excel yoki CSV jadvalini yuklash",
    description="Birinchi ishchi varaq yoki CSV ma'lumotini chat jadvali sifatida saqlaydi.",
)
async def upload_table_endpoint(
    chat_id: int,
    file: UploadFile = File(...),
    browser_id: str = Depends(get_browser_id),
    db: Session = Depends(get_db),
) -> TableResponse:
    """Import a spreadsheet into the selected chat for display and later AI edits."""
    chat = _require_chat(db, chat_id, browser_id)

    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        table_data = read_uploaded_table(filename, content)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    try:
        table = upsert_table(
            db,
            chat_id=chat_id,
            title=table_data["title"],
            columns=table_data["columns"],
            rows=table_data["rows"],
            styles=table_data["styles"],
            source="upload",
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if chat.title == "Yangi chat":
        chat = update_chat(db, chat_id, browser_id, title=table.title)

    create_message(
        db,
        chat_id,
        "user",
        f"Jadval yuklandi: {filename} ({len(table.rows)} qator). "
        "Endi uni chat orqali tahrirlashingiz mumkin.",
    )
    logger.info(
        "Jadval fayldan yuklandi: chat_id=%s, title=%s, rows=%s",
        chat_id,
        table.title,
        len(table.rows),
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
    browser_id: str = Depends(get_browser_id),
    db: Session = Depends(get_db),
) -> TableResponse:
    """Yangi jadval yaratish."""
    _require_chat(db, chat_id, browser_id)
    try:
        table = create_table(
            db,
            chat_id=chat_id,
            title=payload.title,
            columns=payload.columns,
            rows=payload.rows,
            styles=payload.styles,
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
    browser_id: str = Depends(get_browser_id),
    db: Session = Depends(get_db),
) -> TableResponse:
    """Jadvalni yaratish yoki yangilash."""
    _require_chat(db, chat_id, browser_id)
    try:
        table = upsert_table(
            db,
            chat_id=chat_id,
            title=payload.title,
            columns=payload.columns,
            rows=payload.rows,
            styles=payload.styles,
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
    browser_id: str = Depends(get_browser_id),
    db: Session = Depends(get_db),
) -> TableResponse:
    """Jadvalni tahrirlash."""
    _require_chat(db, chat_id, browser_id)

    table = update_table(
        db,
        chat_id=chat_id,
        title=payload.title,
        columns=payload.columns,
        rows=payload.rows,
        styles=payload.styles,
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
    browser_id: str = Depends(get_browser_id),
    db: Session = Depends(get_db),
) -> None:
    """Jadvalni o'chirish."""
    _require_chat(db, chat_id, browser_id)

    deleted = delete_table(db, chat_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bu chatda jadval yo'q: chat_id={chat_id}",
        )