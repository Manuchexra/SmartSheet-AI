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
    _get_demo_edit_response,
    _parse_json_content,
    generate_edit_with_ai,
    generate_with_ai,
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

    def test_non_spreadsheet_prompt_is_preserved_as_one_cell(self):
        """Jadval so'ralmasa, demo uydirma ma'lumot yaratmasligi kerak."""
        result = _get_demo_response("salom")
        assert result.title == "salom"
        assert result.columns == ["Matn"]
        assert result.rows == [["salom"]]

    def test_unmatched_prompt_is_preserved_as_one_cell(self):
        """Mos demo shabloni topilmasa, foydalanuvchi matni saqlanishi kerak."""
        result = _get_demo_response("salom dunyo")
        assert result.title == "salom dunyo"
        assert result.rows == [["salom dunyo"]]

    def test_returns_ai_response(self):
        """Natija AIResponse bo'lishi kerak."""
        result = _get_demo_response("talabalar")
        assert isinstance(result, AIResponse)

    def test_greeting_does_not_call_configured_ai_provider(self, monkeypatch):
        """Salomlashuv AI'ga jadval so'rovi sifatida yuborilmasligi kerak."""
        monkeypatch.setattr(
            "backend.modules.ai.service.is_ai_available",
            lambda: True,
        )
        monkeypatch.setattr(
            "backend.modules.ai.service._call_ai_provider",
            lambda request: pytest.fail("Greeting was sent to the AI provider"),
        )

        response, source = generate_with_ai(AIRequest(prompt="salom"))

        assert source == "demo"
        assert response.title == "salom"
        assert response.columns == ["Matn"]
        assert response.rows == [["salom"]]

    def test_spreadsheet_request_still_calls_configured_ai_provider(self, monkeypatch):
        expected = AIResponse(
            title="Xodimlar",
            columns=["Ism"],
            rows=[["Ali"]],
        )
        monkeypatch.setattr(
            "backend.modules.ai.service.is_ai_available",
            lambda: True,
        )
        monkeypatch.setattr(
            "backend.modules.ai.service._call_ai_provider",
            lambda request: expected,
        )

        response, source = generate_with_ai(
            AIRequest(prompt="Xodimlar jadvali tuz")
        )

        assert source == "ai"
        assert response == expected


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
# AI EDIT
# ============================================
@pytest.mark.unit
class TestAIEdit:
    """Mavjud jadvalni AI orqali tahrirlash."""

    def test_edit_response_uses_existing_values_as_defaults(self, monkeypatch):
        """AI maydonni qaytarmasa, mavjud jadval qiymati saqlansin."""
        existing_table = {
            "title": "Xodimlar",
            "columns": ["Ism", "Maosh"],
            "rows": [["Ali", 5000]],
            "styles": {
                "header": {"bg_color": "#123456"},
                "columns": {"Maosh": {"bg_color": "#16A34A"}},
            },
        }

        class MockResponse:
            status_code = 200

            @staticmethod
            def json():
                return {
                    "choices": [{
                        "message": {
                            "content": '{"rows":[["Ali",5500]]}',
                        },
                    }],
                }

        class MockClient:
            def __init__(self, timeout):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

            @staticmethod
            def post(*args, **kwargs):
                return MockResponse()

        monkeypatch.setattr(
            "backend.modules.ai.service.is_ai_available",
            lambda: True,
        )
        monkeypatch.setattr(
            "backend.modules.ai.service.settings.ai_api_url",
            "https://example.test",
        )
        monkeypatch.setattr(
            "backend.modules.ai.service.httpx.Client",
            MockClient,
        )

        response, source = generate_edit_with_ai(
            "Maoshni oshir",
            existing_table,
        )

        assert source == "ai"
        assert response.title == "Xodimlar"
        assert response.columns == ["Ism", "Maosh"]
        assert response.rows == [["Ali", 5500]]
        assert response.styles.body.border_color == "#000000"
        assert response.styles.header.bg_color == "#123456"
        assert response.styles.columns["Maosh"].bg_color == "#16A34A"

    def test_demo_edit_applies_column_color(self):
        response = _get_demo_edit_response(
            "Maosh ustunini yashil qil",
            {
                "title": "Xodimlar",
                "columns": ["Ism", "Maosh"],
                "rows": [["Ali", 5000]],
                "styles": {},
            },
        )

        assert response.styles.columns["Maosh"].bg_color == "#16A34A"

    def test_ai_edit_targets_header_for_first_visible_row_request(self, monkeypatch):
        class MockResponse:
            status_code = 200

            @staticmethod
            def json():
                return {
                    "choices": [{
                        "message": {
                            "content": (
                                '{"rows":[["Ali",5000]],"styles":'
                                '{"rows":{"0":{"bg_color":"#000000"},'
                                '"1":{"bg_color":"#000000"}}}}'
                            ),
                        },
                    }],
                }

        class MockClient:
            def __init__(self, timeout):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

            @staticmethod
            def post(*args, **kwargs):
                return MockResponse()

        monkeypatch.setattr(
            "backend.modules.ai.service.is_ai_available",
            lambda: True,
        )
        monkeypatch.setattr(
            "backend.modules.ai.service.settings.ai_api_url",
            "https://example.test",
        )
        monkeypatch.setattr(
            "backend.modules.ai.service.httpx.Client",
            MockClient,
        )

        response, source = generate_edit_with_ai(
            "1 - qatorni qora qil dedim ko'kda turganini",
            {
                "title": "Xodimlar",
                "columns": ["Ism", "Maosh"],
                "rows": [["Ali", 5000]],
                "styles": {},
            },
        )

        assert source == "ai"
        assert response.styles.header.bg_color == "#000000"
        assert response.styles.header.text_color == "#FFFFFF"
        assert response.styles.rows == {}


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