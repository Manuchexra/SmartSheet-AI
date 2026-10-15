"""
Excel modulining sxemalari.

Excel eksport so'rovini belgilaydi.
"""

from pydantic import BaseModel, Field
from typing import Any

from backend.modules.styles.defaults import default_styles
from backend.modules.table_generator.schemas import TableData


# ============================================
# EXCEL EKSPORT — SO'ROV
# ============================================
class ExcelExportRequest(BaseModel):
    """
    Excel eksport so'rovi.
    
    Frontend joriy jadval holatini shu formatda yuboradi.
    """
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Jadval nomi (fayl nomi uchun ham ishlatiladi)",
    )
    
    columns: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Ustun sarlavhalari",
    )
    
    rows: list[list[Any]] = Field(
        ...,
        description="Qatorlar ma'lumotlari",
    )

    styles: dict = Field(default_factory=default_styles, description="Jadval uslublari")
    
    def to_table_data(self) -> TableData:
        """
        So'rovni TableData'ga aylantirish.
        
        Bu — validatsiyani qayta ishlatish uchun:
        Excel moduli ham TableData validatsiyasidan o'tadi.
        """
        return TableData(
            title=self.title,
            columns=self.columns,
            rows=self.rows,
            styles=self.styles,
        )