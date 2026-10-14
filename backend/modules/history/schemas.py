"""
History modulining sxemalari.

Undo tarixini boshqarish uchun tuzilmalar.
"""

from datetime import datetime
from pydantic import BaseModel, Field

from backend.modules.table_generator.schemas import TableData


# ============================================
# TARIX YOZUVLARI
# ============================================
class HistoryEntry(BaseModel):
    """
    Tarixdagi bitta holat.
    
    Har bir foydalanuvchi amali (tahrirlash, qator qo'shish/o'chirish)
    shu formatda saqlanadi.
    """
    
    action: str = Field(
        ...,
        description="Amal turi: 'edit', 'add_row', 'delete_row'",
        pattern="^(edit|add_row|delete_row|initial)$",
    )
    
    table_data: TableData = Field(
        ...,
        description="Amaldan oldingi jadval holati",
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Amal vaqti (UTC)",
    )