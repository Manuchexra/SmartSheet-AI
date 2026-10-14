"""
AI moduli testlari.

Bu testlar:
- `_parse_json_content()` ni tekshiradi (markdown, matn, bo'sh)
- `is_ai_available()` ni tekshiradi
- `_get_demo_response()` ni tekshiradi
- AI xatolarini tekshiradi (mock orqali)
"""

import json

import pytest

from backend.modules.ai.schemas import (
    AIError,
    AIInvalidResponseError,
    AIRateLimitError,
    AIRequest,
    AIResponse,
    AITimeoutError,
)
from backend.modules.ai.service import (
    _get_demo_response,
    _parse_json_content,
    is_ai_available,
)


# ============================================
# JSON PARSE — _parse_json_content()
# ============================================
@pytest.mark.unit
class TestParseJsonContent:
    """_parse_json_content funksiyasi."""

    def test_clean_json(self):
        """Toza JSON parse qilinishi kerak."""
        content = '{"title": "Test", "columns": ["A"], "rows": [["1"]]}'
        result = _parse_json_content(content)
        assert result["title"] == "Test"
        assert result["columns"] == ["A"]
        assert result["rows"] == [["1"]]

    def test_json_with_markdown_fence(self):
        """Markdown code fence ichidagi JSON parse qilinishi kerak."""
        content = '```json\n{"title": "Test", "columns": ["A"], "rows": [["1"]]}\n```'
        result = _parse_json_content(content)
        assert result["title"] == "Test"

    def test_json_with_text_before(self):
        """Oldida matn bo'lgan JSON parse qilinishi kerak."""
        content = 'Mana jadval:\n{"title": "Test", "columns": ["A"], "rows": [["1"]]}'
        result = _parse_json_content(content)
        assert result["title"] == "Test"

    def test_json_with_text_after(self):
        """Keyin matn bo'lgan JSON parse qilinishi kerak."""
        content = '{"title": "Test", "columns": ["A"], "rows": [["1"]]}\nUmid qilamiz foydali bo\'ldi.'
        result = _parse_json_content(content)
        assert result["title"] == "Test"

    def test_empty_content(self):
        """Bo'sh content xato berishi kerak."""
        with pytest.raises(AIInvalidResponseError):
            _parse_json_content("")

    def test_whitespace_content(self):
        """Faqat bo'shliq content xato berishi kerak."""
        with pytest.raises(AIInvalidResponseError):
            _parse_json_content("   \n  ")

    def test_no_json(self):
        """JSON bo'lmasa xato berishi kerak."""
        with pytest.raises(AIInvalidResponseError):
            _parse_json_content("Bu JSON emas")

    def test_invalid_json(self):
        """Noto'g'ri JSON xato berishi kerak."""
        with pytest.raises(AIInvalidResponseError):
            _parse_json_content('{"title": "Test", "columns": [')

    def test_nested_json(self):
        """Murakkab JSON parse qilinishi kerak."""
        content = json.dumps({
            "title": "Test",
            "columns": ["A", "B"],
            "rows": [["1", "2"], ["3", "4"]],
            "extra": {"nested": True},
        })
        result = _parse_json_content(content)
        assert result["title"] == "Test"
        assert len(result["rows"]) == 2


# ============================================
# DEMO RESPONSE — _get_demo_response()
# ============================================
@pytest.mark.unit
class TestDemoResponse:
    """_get_demo_response funksiyasi."""

    def test_student_keyword(self):
        """'talaba' kalit so'zi to'g'ri namuna qaytarishi kerak."""
        result = _get_demo_response("talabalar uchun jadval")
        assert "Talaba" in result.title

    def test_employee_keyword(self):
        """'xodim' kalit so'zi to'g'ri namuna qaytarishi kerak."""
        result = _get_demo_response("xodimlar ro'yxati")
        assert "Xodim" in result.title

    def test_product_keyword(self):
        """'mahsulot' kalit so'zi to'g'ri namuna qaytarishi kerak."""
        result = _get_demo_response("mahsulotlar jadvali")
        assert "Mahsulot" in result.title

    def test_project_keyword(self):
        """'loyiha' kalit so'zi to'g'ri namuna qaytarishi kerak."""
        result = _get_demo_response("loyihalar jadvali")
        assert "Loyiha" in result.title

    def test_default(self):
        """Mos kelmagan prompt standart namuna qaytarishi kerak."""
        result = _get_demo_response("salom dunyo")
        assert result.title == "Namunaviy jadval"

    def test_returns_ai_response(self):
        """Natija AIResponse bo'lishi kerak."""
        result = _get_demo_response("talabalar")
        assert isinstance(result, AIResponse)


# ============================================
# AI AVAILABLE — is_ai_available()
# ============================================
@pytest.mark.unit
class TestIsAiAvailable:
    """is_ai_available funksiyasi."""

    def test_no_key(self, monkeypatch):
        """Kalit yo'q bo'lsa, False qaytarishi kerak."""
        monkeypatch.setattr(
            "backend.modules.ai.service.settings.ai_api_key",
            "",
        )
        assert is_ai_available() is False

    def test_no_provider(self, monkeypatch):
        """Provayder yo'q bo'lsa, False qaytarishi kerak."""
        monkeypatch.setattr(
            "backend.modules.ai.service.settings.ai_provider",
            "",
        )
        assert is_ai_available() is False

    def test_demo_provider(self, monkeypatch):
        """Provayder 'demo' bo'lsa, False qaytarishi kerak."""
        monkeypatch.setattr(
            "backend.modules.ai.service.settings.ai_api_key",
            "test-key",
        )
        monkeypatch.setattr(
            "backend.modules.ai.service.settings.ai_provider",
            "demo",
        )
        assert is_ai_available() is False

    def test_ai_available(self, monkeypatch):
        """Kalit va provayder bor bo'lsa, True qaytarishi kerak."""
        monkeypatch.setattr(
            "backend.modules.ai.service.settings.ai_api_key",
            "test-key",
        )
        monkeypatch.setattr(
            "backend.modules.ai.service.settings.ai_provider",
            "groq",
        )
        assert is_ai_available() is True


# ============================================
# AI XATOLARI
# ============================================
@pytest.mark.unit
class TestAIErrors:
    """AI xatolari to'g'ri meros olishi kerak."""

    def test_timeout_error(self):
        err = AITimeoutError()
        assert isinstance(err, AIError)
        assert err.code == "timeout"

    def test_rate_limit_error(self):
        err = AIRateLimitError()
        assert isinstance(err, AIError)
        assert err.code == "rate_limit"

    def test_invalid_response_error(self):
        err = AIInvalidResponseError()
        assert isinstance(err, AIError)
        assert err.code == "invalid_response"

    def test_custom_message(self):
        err = AIError("Custom xato", code="custom")
        assert str(err) == "Custom xato"
        assert err.code == "custom"