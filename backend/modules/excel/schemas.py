"""
Excel modulining sxemalari.

Excel eksport so'rovini belgilaydi.
"""

from pydantic import BaseModel, Field

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
    
    rows: list[list] = Field(
        ...,
        description="Qatorlar ma'lumotlari",
    )
    
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
        )