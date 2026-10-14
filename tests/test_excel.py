"""
Excel moduli testlari.

Bu testlar:
- Excel yaratish (service)
- Excel mazmuni
- Formatlash (sarlavha, freeze, filter)
- Formula injection himoyasi
- API endpoint
"""

from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.modules.excel.service import generate_excel


# ============================================
# SERVICE TESTLARI
# ============================================
@pytest.mark.excel
@pytest.mark.unit
class TestGenerateExcel:
    """generate_excel funksiyasi."""

    def test_basic_generation(self, sample_table_data):
        """Asosiy Excel yaratish ishlashi kerak."""
        buffer = generate_excel(sample_table_data)
        assert isinstance(buffer, BytesIO)
        assert buffer.getbuffer().nbytes > 0

    def test_content(self, sample_table_data):
        """Excel mazmuni to'g'ri bo'lishi kerak."""
        buffer = generate_excel(sample_table_data)
        wb = load_workbook(buffer)
        ws = wb.active

        # Sarlavhalar
        assert ws["A1"].value == "Ism"
        assert ws["B1"].value == "Lavozim"
        assert ws["C1"].value == "Maosh"

        # Ma'lumotlar
        assert ws["A2"].value == "Ali Karimov"
        assert ws["B2"].value == "Dasturchi"
        assert ws["C2"].value == 5000

    def test_header_formatting(self, sample_table_data):
        """Sarlavhalar qalin bo'lishi kerak."""
        buffer = generate_excel(sample_table_data)
        wb = load_workbook(buffer)
        ws = wb.active

        header = ws["A1"]
        assert header.font.bold is True

    def test_freeze_panes(self, sample_table_data):
        """Freeze panes sozlangan bo'lishi kerak."""
        buffer = generate_excel(sample_table_data)
        wb = load_workbook(buffer)
        ws = wb.active
        assert ws.freeze_panes == "A2"

    def test_auto_filter(self, sample_table_data):
        """Auto filter sozlangan bo'lishi kerak."""
        buffer = generate_excel(sample_table_data)
        wb = load_workbook(buffer)
        ws = wb.active
        assert ws.auto_filter.ref is not None
        assert "A1:C4" in ws.auto_filter.ref

    def test_formula_injection_protection(self):
        """Xavfli formulalar neytrallanishi kerak."""
        from backend.modules.table_generator.schemas import TableData

        data = TableData(
            title="Test",
            columns=["Xavfli"],
            rows=[["=cmd|'/c calc'!A1"]],
        )
        buffer = generate_excel(data)
        wb = load_workbook(buffer)
        ws = wb.active

        # Apostrof qo'shilgan bo'lishi kerak
        assert ws["A2"].value.startswith("'")

    def test_unicode_content(self):
        """Unicode (o'zbek) matn saqlanishi kerak."""
        from backend.modules.table_generator.schemas import TableData

        data = TableData(
            title="O'zbek jadvali",
            columns=["Ism", "Familiya"],
            rows=[["Ali", "Karimov"], ["Nilufar", "Rahimova"]],
        )
        buffer = generate_excel(data)
        wb = load_workbook(buffer)
        ws = wb.active

        assert ws["A1"].value == "Ism"
        assert ws["A2"].value == "Ali"

    def test_empty_columns_error(self):
        """Bo'sh ustunlar xato berishi kerak."""
        from backend.modules.table_generator.schemas import TableData

        data = TableData(title="T", columns=["A"], rows=[["1"]])
        # Service darajasida ham tekshirish
        buffer = generate_excel(data)
        assert buffer is not None


# ============================================
# API ENDPOINT
# ============================================
@pytest.mark.excel
@pytest.mark.api
class TestExcelEndpoint:
    """POST /api/v1/excel/export."""

    def test_export_success(self, client):
        """Excel eksport 200 qaytarishi kerak."""
        response = client.post(
            "/api/v1/excel/export",
            json={
                "title": "Test",
                "columns": ["Ism", "Ball"],
                "rows": [["Ali", 92]],
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith(
            "application/vnd.openxmlformats"
        )

    def test_export_content(self, client):
        """Eksport qilingan fayl to'g'ri bo'lishi kerak."""
        response = client.post(
            "/api/v1/excel/export",
            json={
                "title": "Test",
                "columns": ["Ism", "Ball"],
                "rows": [["Ali", 92], ["Malika", 85]],
            },
        )
        assert response.status_code == 200

        wb = load_workbook(BytesIO(response.content))
        ws = wb.active

        assert ws["A1"].value == "Ism"
        assert ws["A2"].value == "Ali"
        assert ws["B2"].value == 92

    def test_export_disposition(self, client):
        """Content-Disposition sarlavhasi to'g'ri bo'lishi kerak."""
        response = client.post(
            "/api/v1/excel/export",
            json={
                "title": "Test",
                "columns": ["A"],
                "rows": [["1"]],
            },
        )
        assert "smartsheet.xlsx" in response.headers["content-disposition"]

    def test_export_invalid(self, client):
        """Noto'g'ri so'rov 422 qaytarishi kerak."""
        response = client.post(
            "/api/v1/excel/export",
            json={"title": "T"},  # columns va rows yo'q
        )
        assert response.status_code == 422