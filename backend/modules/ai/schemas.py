"""
AI modulining sxemalari.

Bu modul AI provayderiga yuboriladigan so'rovni va
AI'dan keladigan javobni belgilaydi.
"""

from pydantic import BaseModel, Field


# ============================================
# AI'GA SO'ROV
# ============================================
class AIRequest(BaseModel):
    """
    AI provayderiga yuboriladigan so'rov.
    
    Bizning backend AI'ga shu formatda murojaat qiladi.
    """
    
    prompt: str = Field(
        ...,
        min_length=3,
        description="Foydalanuvchining tabiiy tildagi so'rovi",
    )
    
    max_rows: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="AI yaratishi mumkin bo'lgan maksimal qatorlar soni",
    )
    
    max_columns: int = Field(
        default=20,
        ge=1,
        le=100,
        description="AI yaratishi mumkin bo'lgan maksimal ustunlar soni",
    )


# ============================================
# AI'DAN JAVOB
# ============================================
class AIResponse(BaseModel):
    """
    AI provayderidan keladigan xom javob.
    
    Diqqat: bu AI'ning xom javobi. U hali to'liq
    validatsiyadan o'tmagan. TableData'ga aylantirishdan
    oldin Table Generator moduli tekshiradi.
    """
    
    title: str = Field(
        ...,
        description="AI taklif qilgan jadval nomi",
    )
    
    columns: list[str] = Field(
        ...,
        min_length=1,
        description="AI taklif qilgan ustunlar",
    )
    
    rows: list[list] = Field(
        ...,
        min_length=1,
        description="AI yaratgan qatorlar",
    )