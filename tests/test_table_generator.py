"""
Table Generator moduli testlari.

Bu testlar TableData validatsiyasini, build_table_response'ni
va limitlarni tekshiradi.
"""

import pytest
from pydantic import ValidationError

from backend.modules.table_generator.schemas import (
    TableData,
    TableGenerateRequest,
    TableGenerateResponse,
)
from backend.modules.table_generator.service import build_table_response
from backend.modules.ai.schemas import AIRequest
from backend.config import settings


# ============================================
# TableData — VALIDATSIYA TESTLARI
# ============================================
@pytest.mark.unit
class TestTableDataValidation:
    """TableData validatsiyasi."""

    def test_valid_table(self):
        """To'g'ri jadval qabul qilinishi kerak."""
        data = TableData(
            title="Test",
            columns=["A", "B"],
            rows=[["1", "2"]],
        )
        assert data.title == "Test"
        assert data.row_count == 1
        assert data.column_count == 2

    def test_empty_title(self):
        """Bo'sh title xato berishi kerak."""
        with pytest.raises(ValidationError):
            TableData(title="   ", columns=["A"], rows=[["1"]])

    def test_empty_columns(self):
        """Bo'sh ustunlar xato berishi kerak."""
        with pytest.raises(ValidationError):
            TableData(title="T", columns=[], rows=[["1"]])

    def test_empty_rows(self):
        """Bo'sh qatorlar xato berishi kerak."""
        with pytest.raises(ValidationError):
            TableData(title="T", columns=["A"], rows=[])

    def test_column_row_mismatch(self):
        """Ustun-qator mos kelmasa xato berishi kerak."""
        with pytest.raises(ValidationError):
            TableData(
                title="T",
                columns=["A", "B", "C"],
                rows=[["1", "2"]],  # 2 qiymat, 3 kutilgan
            )

    def test_duplicate_columns(self):
        """Takrorlangan ustunlar xato berishi kerak."""
        with pytest.raises(ValidationError):
            TableData(
                title="T",
                columns=["A", "A"],
                rows=[["1", "2"]],
            )

    def test_title_trimmed(self):
        """Title atrofidagi bo'shliqlar olib tashlanishi kerak."""
        data = TableData(
            title="  Test  ",
            columns=["A"],
            rows=[["1"]],
        )
        assert data.title == "Test"

    def test_max_columns_limit(self):
        """Juda ko'p ustunlar xato berishi kerak."""
        with pytest.raises(ValidationError):
            TableData(
                title="T",
                columns=[f"C{i}" for i in range(25)],  # > 20
                rows=[["1"] * 25],
            )

    def test_accepts_200_rows(self, monkeypatch):
        monkeypatch.setattr(settings, "max_rows", 200)
        data = TableData(
            title="200 qator",
            columns=["Qiymat"],
            rows=[[row] for row in range(200)],
        )
        assert data.row_count == 200

    def test_rejects_more_than_200_rows(self, monkeypatch):
        monkeypatch.setattr(settings, "max_rows", 200)
        with pytest.raises(ValidationError, match="200 tadan oshmasligi"):
            TableData(
                title="201 qator",
                columns=["Qiymat"],
                rows=[[row] for row in range(201)],
            )


@pytest.mark.unit
class TestAIRowLimit:
    def test_default_limit_is_200(self):
        assert AIRequest(prompt="Jadval yarat").max_rows == 200

    def test_limit_cannot_exceed_200(self):
        with pytest.raises(ValidationError):
            AIRequest(prompt="Jadval yarat", max_rows=201)


# ============================================
# TableGenerateRequest — VALIDATSIYA
# ============================================
@pytest.mark.unit
class TestTableGenerateRequest:
    """TableGenerateRequest validatsiyasi."""

    def test_valid_prompt(self):
        """To'g'ri prompt qabul qilinishi kerak."""
        req = TableGenerateRequest(prompt="Test prompt")
        assert req.prompt == "Test prompt"

    def test_empty_prompt(self):
        """Bo'sh prompt xato berishi kerak."""
        with pytest.raises(ValidationError):
            TableGenerateRequest(prompt="   ")

    def test_short_prompt(self):
        """Juda qisqa prompt xato berishi kerak."""
        with pytest.raises(ValidationError):
            TableGenerateRequest(prompt="ab")

    def test_long_prompt(self):
        """Juda uzun prompt xato berishi kerak."""
        with pytest.raises(ValidationError):
            TableGenerateRequest(prompt="a" * 3000)

    def test_prompt_trimmed(self):
        """Prompt atrofidagi bo'shliqlar olib tashlanishi kerak."""
        req = TableGenerateRequest(prompt="  Test  ")
        assert req.prompt == "Test"


# ============================================
# build_table_response — INTEGRATION
# ============================================
@pytest.mark.unit
class TestBuildTableResponse:
    """build_table_response funksiyasi."""

    def test_build_success(self, sample_ai_response):
        """AI javobidan response qurilishi kerak."""
        response = build_table_response(sample_ai_response, source="ai")
        assert response.title == sample_ai_response.title
        assert response.row_count == len(sample_ai_response.rows)
        assert response.column_count == len(sample_ai_response.columns)
        assert response.source == "ai"

    def test_build_demo_source(self, sample_ai_response):
        """source='demo' bo'lsa, shunday saqlanishi kerak."""
        response = build_table_response(sample_ai_response, source="demo")
        assert response.source == "demo"

    def test_build_invalid_source(self, sample_ai_response):
        """Noto'g'ri source xato berishi kerak."""
        with pytest.raises(ValidationError):
            build_table_response(sample_ai_response, source="invalid")


# ============================================
# TableGenerateResponse — YORDAMCHI
# ============================================
@pytest.mark.unit
class TestTableGenerateResponse:
    """TableGenerateResponse yordamchi metodlari."""

    def test_from_table_data(self, sample_table_data):
        """TableData'dan response yaratilishi kerak."""
        response = TableGenerateResponse.from_table_data(
            sample_table_data, source="demo"
        )
        assert response.title == sample_table_data.title
        assert response.row_count == sample_table_data.row_count
        assert response.column_count == sample_table_data.column_count
        assert response.source == "demo"